from .._shared import *


class _GenerateMediumGrainedCategoriesMixin:
    def _generate_medium_grained_categories(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成中等粒度分类 - 连续谱系版本
        """
        if not resources:
            return {
                "核心主题资源": [],
                "相关主题资源": [],
                "扩展主题资源": []
            }
        
        # 计算得分范围
        scores = [resource.get("overall_score", resource.get("relevance", 0)) for resource in resources]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        # 基于连续分布的分类阈值
        core_threshold = max_score - score_range * 0.3  # 前30%为核心资源
        related_threshold = max_score - score_range * 0.7  # 30%-70%为相关资源
        
        categories = {
            "核心主题资源": [],
            "相关主题资源": [],
            "扩展主题资源": []
        }
        
        for resource in resources:
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            match_level = resource.get("match_level", "none")
            
            if match_level == "core" or overall_score >= core_threshold:
                categories["核心主题资源"].append(resource)
            elif match_level == "related" or overall_score >= related_threshold:
                categories["相关主题资源"].append(resource)
            else:
                categories["扩展主题资源"].append(resource)
        
        # 确保核心主题资源至少有一个（如果有资源的话）
        if not categories["核心主题资源"] and resources:
            categories["核心主题资源"].append(resources[0])
            if categories["相关主题资源"]:
                categories["相关主题资源"].pop(0)
        
        return categories
