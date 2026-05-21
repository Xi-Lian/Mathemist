from ..._shared import *
from .common import build_match_result, has_theme_text_hit, is_specific_theme_query
from ...evaluation.courseware_evaluator import get_courseware_evaluator


def evaluate_non_exercise_match(retriever, doc, metadata, base_relevance, resource_type, core_theme, query=""):
    """
    评估非习题资源（教案、课件等）
    """
    print(f"   🔍 [V42.0 DEBUG] evaluate_non_exercise_match被调用: resource_type={resource_type}, core_theme={core_theme}")
    print(f"   🔍 [V42.0 DEBUG] 标题: {metadata.get('title', '未知')[:60]}")
    print(f"   🔍 [V42.0 DEBUG] 教学用途: {metadata.get('教学用途', '')}")
    
    # ========== 课件使用新的三字段评估器 ==========
    if resource_type == "courseware":
        print(f"   🔍 [V42.0 DEBUG] 进入课件评估逻辑")
        try:
            evaluator = get_courseware_evaluator()
            
            # 获取向量距离（从base_relevance反推）
            distance = (1.0 - base_relevance) * 2 if base_relevance <= 1.0 else 0.0
            print(f"   🔍 [V42.0 DEBUG] base_relevance={base_relevance:.3f}, distance={distance:.3f}")
            
            final_score, should_show, details = evaluator.evaluate(
                metadata=metadata,
                doc=doc,
                distance=distance,
                core_theme=core_theme,
                query=query,
                context=None
            )
            
            print(f"   📊 [V42.0 DEBUG] 课件三字段评分:")
            print(f"      基础向量: {details['base_relevance']:.3f}")
            print(f"      文件名: {details['filename_score']:.3f}")
            print(f"      教学用途: {details['teaching_use_score']:.3f}")
            print(f"      内容: {details['content_score']:.3f}")
            print(f"      最终得分: {final_score:.3f} (阈值: {details['threshold']:.3f})")
            print(f"      结果: {'✅ 展示' if should_show else '❌ 隐藏'}")
            if not should_show and 'reject_reason' in details:
                print(f"      拒绝原因: {details['reject_reason']}")
            
            return build_match_result(
                [core_theme] if core_theme else [],
                core_theme,
                [],
                True,
                "core",
                resource_type,
                f"课件三字段评估得分: {final_score:.3f}",
                should_show,
                final_score
            )
        except Exception as e:
            print(f"   ⚠️ 课件评估器异常，使用降级逻辑: {e}")
            # 降级到原有逻辑
    
    # ========== 其他资源类型保持原有逻辑 ==========
    theme_matcher_v90 = get_theme_matcher_v90()
    specific_theme_query = is_specific_theme_query(core_theme)

    if resource_type == "lesson_plan":
        precise_match_result = theme_matcher_v90.calculate_precise_match(
            query=core_theme,
            lesson_title=metadata.get("title", ""),
            lesson_content=doc,
            metadata=metadata,
        )
        # 对 V90 主题体系未覆盖的新板块，允许基于标题/路径/标签/正文的直接命中兜底展示。
        text_hit = has_theme_text_hit(core_theme, metadata, doc)
        if specific_theme_query and not precise_match_result["is_core_match"] and text_hit:
            precise_match_result["matched_themes"] = [theme for theme in core_theme.split(",") if theme.strip()]
            precise_match_result["core_theme"] = precise_match_result["matched_themes"][0] if precise_match_result["matched_themes"] else core_theme
            precise_match_result["related_themes"] = precise_match_result["matched_themes"][1:] if len(precise_match_result["matched_themes"]) > 1 else []
            precise_match_result["is_core_match"] = True
            precise_match_result["match_level"] = "core"
            precise_match_result["should_show"] = True
            precise_match_result["relevance_score"] = max(precise_match_result.get("relevance_score", 0.0), 0.85)
            precise_match_result["overall_score"] = max(precise_match_result.get("overall_score", 0.0), precise_match_result["relevance_score"])
            precise_match_result["explanation"] = f"文本直接命中主题：{core_theme}"
        elif specific_theme_query and not precise_match_result["is_core_match"] and precise_match_result["match_level"] not in {"related", "extended"}:
            precise_match_result["should_show"] = False
            precise_match_result["relevance_score"] = 0.0
            precise_match_result["overall_score"] = 0.0
            precise_match_result["match_level"] = "none"
            precise_match_result["explanation"] = f"明确主题查询未命中主题：{core_theme}"
        return {
            "matched_themes": precise_match_result["matched_themes"],
            "core_theme_match": precise_match_result["core_theme"],
            "related_themes": precise_match_result["related_themes"],
            "mentioned_themes": precise_match_result["mentioned_themes"],
            "is_core_match": precise_match_result["is_core_match"],
            "match_level": precise_match_result["match_level"],
            "domain": precise_match_result["domain"],
            "explanation": precise_match_result["explanation"],
            "should_show": precise_match_result["should_show"],
            "relevance_score": precise_match_result["relevance_score"],
            "overall_score": precise_match_result.get("overall_score", precise_match_result["relevance_score"]),
            "resource_quality": precise_match_result.get("resource_quality", None),
            "content_completeness": precise_match_result.get("content_completeness", None),
            "teaching_value": precise_match_result.get("teaching_value", None),
            "comprehensiveness": precise_match_result.get("comprehensiveness", None),
            "concept_hierarchy_factor": precise_match_result.get("concept_hierarchy_factor", 0.5),
        }

    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    matched_themes = [theme for theme in query_themes if theme in doc or theme in metadata.get("title", "")]
    theme_keywords = []
    for theme in query_themes:
        theme_keywords.extend(retriever.config_loader.get_theme_keywords(theme))
    matched_keywords = [keyword for keyword in theme_keywords if keyword in doc or keyword in metadata.get("title", "")]

    if resource_type in {"courseware", "exercise"}:
        return evaluate_keyword_based_match(base_relevance, resource_type, query_themes, matched_keywords, theme_keywords)
    if matched_themes:
        return build_match_result(matched_themes, matched_themes[0], matched_themes[1:] if len(matched_themes) > 1 else [], True, "core", resource_type, f"匹配到主题: {', '.join(matched_themes)}", True, base_relevance)
    if specific_theme_query and not has_theme_text_hit(core_theme, metadata, doc):
        return build_match_result([], None, [], False, "none", resource_type, f"明确主题查询未命中主题：{core_theme}", False, 0.0)
    return build_match_result([], None, [], False, "related", resource_type, "基于向量相似度匹配", base_relevance > 0.30, base_relevance * 0.5)


def evaluate_keyword_based_match(base_relevance, resource_type, query_themes, matched_keywords, theme_keywords, metadata=None, doc=None, distance=None, core_theme=None, query=None):
    """关键词匹配评估（课件已在上层使用新评估器，这里保留作为降级方案）"""
    specific_theme_query = is_specific_theme_query(",".join(query_themes))
    if matched_keywords:
        keyword_match_score = min(len(matched_keywords) / max(len(theme_keywords), 1), 1.0)
        should_show = keyword_match_score >= (0.2 if resource_type == "courseware" else 0.3)
        return build_match_result(
            query_themes,
            query_themes[0] if query_themes else None,
            query_themes[1:] if len(query_themes) > 1 else [],
            True,
            "core",
            resource_type,
            f"匹配到主题关键词: {', '.join(matched_keywords[:5])}",
            should_show,
            base_relevance * (0.7 + 0.3 * keyword_match_score),
        )
    if specific_theme_query:
        return build_match_result([], None, [], False, "none", resource_type, "明确主题查询未命中主题关键词", False, 0.0)
    should_show = base_relevance > (0.10 if resource_type == "courseware" else 0.30)
    return build_match_result([], None, [], False, "related", resource_type, "基于向量相似度匹配", should_show, base_relevance * 0.5)
