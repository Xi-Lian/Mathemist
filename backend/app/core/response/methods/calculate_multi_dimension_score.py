from .._shared import *


class _CalculateMultiDimensionScoreMixin:
    def _calculate_multi_dimension_score(self, resource: Dict[str, Any]) -> float:
        """
        V10.0：计算多维度综合得分
        
        Args:
            resource: 资源字典
            
        Returns:
            综合得分
        """
        # 从资源中提取各项指标
        relevance = resource.get("relevance", resource.get("relevance_score", 0))
        
        # 优先使用主题匹配器计算的评估指标
        resource_quality = resource.get("resource_quality", None)
        content_completeness = resource.get("content_completeness", None)
        teaching_value = resource.get("teaching_value", None)
        comprehensiveness = resource.get("comprehensiveness", None)
        
        # 如果没有评估指标，使用默认值
        if resource_quality is None:
            resource_quality = 0.5
        if content_completeness is None:
            content_completeness = 0.5
        if teaching_value is None:
            teaching_value = 0.5
        if comprehensiveness is None:
            comprehensiveness = 0.5
        
        # 权重配置
        weights = {
            "relevance": 0.4,      # 相关性权重
            "quality": 0.2,        # 资源质量权重
            "completeness": 0.15,  # 内容完整性权重
            "teaching": 0.15,      # 教学价值权重
            "comprehensive": 0.1   # 综合性权重
        }
        
        # 计算加权和
        total_score = (
            relevance * weights["relevance"] +
            resource_quality * weights["quality"] +
            content_completeness * weights["completeness"] +
            teaching_value * weights["teaching"] +
            comprehensiveness * weights["comprehensive"]
        )
        
        return total_score
