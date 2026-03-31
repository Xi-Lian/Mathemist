from .._shared import *


class _CalculateOverallScoreMixin:
    def _calculate_overall_score(self, relevance_score: float, resource_quality: float, content_completeness: float, teaching_value: float, comprehensiveness: float) -> float:
        """
        V10.0：计算综合得分
        V62.0改进：当relevance_score为0时，overall_score也应该为0
        
        Args:
            relevance_score: 相关性分数
            resource_quality: 资源质量
            content_completeness: 内容完整性
            teaching_value: 教学价值
            comprehensiveness: 综合性
            
        Returns:
            综合得分
        """
        # V62.0改进：如果相关性分数为0，则综合得分也为0
        if relevance_score == 0.0:
            return 0.0
        
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
            relevance_score * weights["relevance"] +
            resource_quality * weights["quality"] +
            content_completeness * weights["completeness"] +
            teaching_value * weights["teaching"] +
            comprehensiveness * weights["comprehensive"]
        )
        
        return total_score
