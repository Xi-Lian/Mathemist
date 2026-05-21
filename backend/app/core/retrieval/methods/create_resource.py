from .._shared import *
from ..create_resource_helpers.evaluation import evaluate_resource_match
from ..create_resource_helpers.finalize import (
    apply_quality_controls,
    apply_relevance_thresholds,
    run_resource_processors,
    update_resource_with_match,
)


class _CreateResourceMixin:
    def _create_resource(
        self,
        doc: str,
        metadata: Dict[str, Any],
        distance: float,
        resource_type: str,
        core_theme: str = "",
        resource_types: List[str] = None,
        query: str = "",
        question_type: str = "",
    ) -> Dict[str, Any]:
        """
        创建资源对象（带主题匹配）- V2改进版
        使用置信度评估和主题组合合理性检查
        """
        base_relevance = 1 / (1 + distance)
        difficulty = metadata.get("难度", "") or metadata.get("difficulty", "") or metadata.get("难度（1-5）", "")
        resolved_question_type = metadata.get("题目类型", "")
        knowledge_points = metadata.get("知识点", "") or metadata.get("知识点标签", "")

        resource = {
            "title": metadata.get("title", "未知"),
            "content": doc,
            "source": metadata.get("原文件云端链接", "") or metadata.get("云端链接", "") or metadata.get("source_file", ""),
            "relevance": base_relevance,
            "metadata": metadata,
            "base_relevance": base_relevance,
            "theme_match": False,
            "type_match": False,
            "matched_theme_count": 0,
            "theme_boost": 0.0,
            "conflict_theme": False,
            "matched_themes": [],
            "is_comprehensive": False,
            "难度": difficulty,
            "题目类型": resolved_question_type,
            "知识点": knowledge_points,
            "multi_theme_retrieval_info": {
                "matched_themes": metadata.get("_matched_themes", []),
                "matched_theme_count": metadata.get("_matched_theme_count", 0),
                "theme_distances": metadata.get("_theme_distances", {}),
            },
        }

        match_result = evaluate_resource_match(
            self,
            doc,
            metadata,
            base_relevance,
            resource_type,
            core_theme,
            query,
            question_type,
        )
        resource["match_result"] = match_result
        # V311.0改进：传递metadata，以便在分别查询模式下能够保留_matched_themes信息
        update_resource_with_match(resource, match_result, metadata)
        apply_relevance_thresholds(resource, resource_type, resource_types)
        run_resource_processors(self, resource, metadata, resource_type)
        apply_quality_controls(self, resource, resource_type)
        resource.pop("match_result", None)
        return resource
