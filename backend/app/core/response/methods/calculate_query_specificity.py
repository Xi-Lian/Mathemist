from .._shared import *


class _CalculateQuerySpecificityMixin:
    def _calculate_query_specificity(self, query: str) -> float:
        """
        计算查询的具体程度
        
        Args:
            query: 用户查询
            
        Returns:
            具体程度分数 (0-1)
        """
        if not query:
            return 0.0
        
        # 关键词数量
        words = query.split()
        word_count = len(words)
        
        # 具体关键词权重
        specific_keywords = [
            "概念", "性质", "图像", "应用", "计算", "公式", "定理",
            "单调性", "奇偶性", "周期性", "定义域", "值域", "最大值", "最小值"
        ]
        
        # 计算具体程度分数
        specificity = 0.0
        
        # 基于词数的分数 (0-0.5)
        if word_count >= 5:
            specificity += 0.5
        elif word_count >= 3:
            specificity += 0.3
        elif word_count >= 2:
            specificity += 0.1
        
        # 基于具体关键词的分数 (0-0.5)
        for keyword in specific_keywords:
            if keyword in query:
                specificity += 0.1
                if specificity >= 1.0:
                    break
        
        return min(1.0, specificity)
