from .._shared import *


class _CalculateQueryClarityMixin:
    def _calculate_query_clarity(self, query: str, core_concepts: List[str], intent: Dict[str, Any]) -> float:
        """
        计算查询明确度（0-1）
        """
        clarity = 0.0
        
        if core_concepts:
            clarity += 0.3
        
        if intent["resource_types"]:
            clarity += 0.2
        
        qualifier_words = ["二次", "指数", "对数", "三角", "一元", "二元", "偏导", "定积分", "不定积分"]
        for word in qualifier_words:
            if word in query:
                clarity += 0.2
                break
        
        query_length = len(query)
        if 10 <= query_length <= 30:
            clarity += 0.2
        elif query_length > 30:
            clarity += 0.1
        
        if "$" in query or "\\(" in query or "\\[" in query:
            clarity += 0.1
        
        return min(1.0, clarity)
