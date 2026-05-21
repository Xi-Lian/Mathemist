import logging
from .._shared import *
from ..consistency_helpers.context import (
    build_consistency_context,
    extract_specific_knowledge_points,
    should_skip_consistency_check,
)
from ..consistency_helpers.matching import contains_conflicting_theme, has_knowledge_match
from ..consistency_helpers.paths import has_path_conflict

_log = logging.getLogger(__name__)

# 延迟加载知识图谱，避免循环导入
_KG_INSTANCE = None

def _get_knowledge_graph():
    global _KG_INSTANCE
    if _KG_INSTANCE is None:
        try:
            from backend.app.core.knowledge_graph import KnowledgeGraph
            import os
            graph_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
                'knowledge_graph.json'
            )
            _KG_INSTANCE = KnowledgeGraph(graph_path=graph_path)
        except Exception as e:
            print(f"   ⚠️ 知识图谱加载失败: {e}")
            _KG_INSTANCE = None
    return _KG_INSTANCE


class _CheckKnowledgePointConsistencyMixin:
    def _check_knowledge_point_consistency(
        self,
        metadata: Dict[str, Any],
        core_theme: str,
        doc: str = "",
        query: str = "",
        relevance: float = 0.0,
    ) -> bool:
        """
        V16.0: 检查习题的知识点是否与查询要求一致。
        改进：用知识图谱层级关系扩展关键词，使"三角恒等变换"能匹配所有后代节点（二倍角、诱导公式等）。
        """
        if not core_theme:
            return True

        context = build_consistency_context(metadata, core_theme, doc, query, relevance)
        themes = context["themes"]
        if should_skip_consistency_check(core_theme, relevance, themes):
            return True

        # ── 原有逻辑：从 themes 提取具体知识点 ──
        specific_knowledge_points = extract_specific_knowledge_points(themes)

        # ── 新增：用知识图谱扩展关键词 ──
        kg_expanded = self._expand_themes_via_kg(core_theme, themes)
        specific_knowledge_points = list(set(specific_knowledge_points + kg_expanded))
        _log.warning(
            f"[方案A调试] 扩展后关键词({len(specific_knowledge_points)}个): "
            f"{specific_knowledge_points[:10]}"
        )

        if has_path_conflict(self, metadata, specific_knowledge_points, context["source_file"], relevance):
            _log.warning(f"[方案A调试] 路径冲突，跳过: source={context['source_file'][:60]}")
            return False

        has_match = has_knowledge_match(
            self,
            specific_knowledge_points,
            context["knowledge_tags"],
            context["source_file"],
            context["title"],
            context["question_content"],
            context["question_file"],
        )
        _log.warning(
            f"[方案A调试] has_match={has_match}, knowledge_tags={context['knowledge_tags']}, "
            f"title={context['title']}, relevance={relevance:.3f}"
        )
        if has_match:
            return True

        if contains_conflicting_theme(self, specific_knowledge_points, context["all_info"], relevance):
            _log.warning(f"[方案A调试] 冲突主题，跳过: title={context['title']}")
            return False

        result = relevance > 0.6
        _log.warning(f"[方案A调试] 最终判断: relevance={relevance:.3f} > 0.6 = {result}")
        return result

    def _expand_themes_via_kg(self, core_theme: str, themes: List[str]) -> List[str]:
        """
        用知识图谱扩展主题关键词：
        对每个 theme，在知识图谱中查找匹配节点，收集其所有后代节点的 label 和 keywords。
        """
        kg = _get_knowledge_graph()
        if kg is None:
            print("   ⚠️ 知识图谱不可用，跳过扩展")
            return []

        expanded = set()
        # 对每个主题都做扩展
        all_themes = [core_theme] + themes
        for theme in all_themes:
            if not theme:
                continue
            try:
                result = kg.get_descendant_labels_and_keywords(theme)
                labels = result.get("labels", [])
                keywords = result.get("keywords", [])
                expanded.update(labels)
                expanded.update(keywords)
                if labels or keywords:
                    print(f"   🔗 知识图谱扩展 '{theme}': {len(labels)}个标签, {len(keywords)}个关键词")
            except Exception as e:
                print(f"   ⚠️ 知识图谱扩展 '{theme}' 失败: {e}")

        # 过滤掉过于通用的词（避免误匹配）
        filtered = []
        for word in expanded:
            w = word.strip()
            if len(w) >= 2:   # 至少2个字
                filtered.append(w)
        return filtered
