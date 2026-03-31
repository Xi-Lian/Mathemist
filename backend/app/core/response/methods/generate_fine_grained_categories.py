from .._shared import *


class _GenerateFineGrainedCategoriesMixin:
    def _generate_fine_grained_categories(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成细粒度分类 - 连续谱系版本
        """
        if not resources:
            return {
                "核心概念资源": [],
                "重点性质资源": [],
                "应用实例资源": [],
                "扩展参考资源": []
            }
        
        # 计算得分范围
        scores = [resource.get("overall_score", resource.get("relevance", 0)) for resource in resources]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        # 基于连续分布的分类阈值
        high_threshold = max_score - score_range * 0.4  # 前40%为高相关资源
        medium_threshold = max_score - score_range * 0.7  # 40%-70%为中等相关资源
        
        categories = {
            "核心概念资源": [],
            "重点性质资源": [],
            "应用实例资源": [],
            "扩展参考资源": []
        }
        
        for resource in resources:
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            title = resource.get("title", "")
            content = resource.get("content", "")
            
            # 基于内容特征进行细粒度分类
            full_text = f"{title} {content}"
            
            if overall_score >= high_threshold:
                if any(keyword in full_text for keyword in ["概念", "定义", "含义"]):
                    categories["核心概念资源"].append(resource)
                elif any(keyword in full_text for keyword in ["性质", "定理", "法则"]):
                    categories["重点性质资源"].append(resource)
                elif any(keyword in full_text for keyword in ["应用", "实例", "例子"]):
                    categories["应用实例资源"].append(resource)
                else:
                    categories["核心概念资源"].append(resource)
            elif overall_score >= medium_threshold:
                if any(keyword in full_text for keyword in ["概念", "定义"]):
                    categories["核心概念资源"].append(resource)
                elif any(keyword in full_text for keyword in ["性质", "定理"]):
                    categories["重点性质资源"].append(resource)
                elif any(keyword in full_text for keyword in ["应用", "实例"]):
                    categories["应用实例资源"].append(resource)
                else:
                    categories["扩展参考资源"].append(resource)
            else:
                categories["扩展参考资源"].append(resource)
        
        return categories
