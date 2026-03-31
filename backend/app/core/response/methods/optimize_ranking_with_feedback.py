from .._shared import *


class _OptimizeRankingWithFeedbackMixin:
    def _optimize_ranking_with_feedback(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        V10.0：使用用户反馈优化排序
        
        Args:
            resources: 资源列表
            
        Returns:
            优化排序后的资源列表
        """
        # 为每个资源添加反馈得分
        for resource in resources:
            resource_id = resource.get("id", str(hash(resource.get("title", ""))))
            feedback_data = self._analyze_feedback_data(resource_id)
            
            # 计算反馈得分
            feedback_score = (
                feedback_data.get("click_rate", 0.5) * 0.3 +
                feedback_data.get("view_duration", 0.5) * 0.2 +
                feedback_data.get("download_rate", 0.5) * 0.3 +
                feedback_data.get("satisfaction_score", 0.5) * 0.2
            )
            
            # 结合反馈得分优化综合得分
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            optimized_score = overall_score * 0.7 + feedback_score * 0.3
            resource["optimized_score"] = optimized_score
        
        # 基于优化后的得分排序
        sorted_resources = sorted(
            resources,
            key=lambda x: (-x.get("optimized_score", x.get("overall_score", 0)),
                          -x.get("overall_score", x.get("relevance", 0)))
        )
        
        return sorted_resources
