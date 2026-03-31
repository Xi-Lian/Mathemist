from .._shared import *


class _CalculateOverallScoreMixin:
    def _calculate_overall_score(self, resource: Dict[str, Any], is_core_match: bool) -> float:
        """
        计算资源的综合得分
        
        Args:
            resource: 资源对象
            is_core_match: 是否是核心主题匹配
        
        Returns:
            综合得分
        """
        relevance = resource.get('relevance', 0.0)
        resource_quality = resource.get('resource_quality', 0.0)
        content_completeness = resource.get('content_completeness', 0.0)
        teaching_value = resource.get('teaching_value', 0.0)
        comprehensiveness = resource.get('comprehensiveness', 0.0)
        concept_hierarchy_factor = resource.get('concept_hierarchy_factor', 0.5)
        
        # 综合得分计算公式
        # 相关性占主要权重，其他指标作为辅助
        overall_score = (
            relevance * 0.5 +
            resource_quality * 0.15 +
            content_completeness * 0.15 +
            teaching_value * 0.1 +
            comprehensiveness * 0.1
        )
        
        # 如果是核心主题匹配，给予额外加分
        if is_core_match:
            overall_score *= 1.1
        
        # 确保得分在0-1之间
        overall_score = max(0.0, min(1.0, overall_score))
        
        return overall_score
