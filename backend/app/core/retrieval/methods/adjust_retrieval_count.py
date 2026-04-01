from .._shared import *


class _AdjustRetrievalCountMixin:
    def _adjust_retrieval_count(self, query: str, detected_intents: List[Dict[str, Any]], base_count: int, resource_types: List[str] = None) -> int:
        """
        根据检测到的意图动态调整检索数量
        
        Args:
            query: 用户查询
            detected_intents: 检测到的意图列表
            base_count: 基础检索数量
            
        Returns:
            调整后的检索数量
        """
        adjusted_count = base_count
        max_priority = max((i.get("priority", 0) for i in detected_intents), default=0)
        high_priority_count = sum(1 for i in detected_intents if i.get("priority", 0) >= 9)
        query_len = len(query or "")
        type_count = len(resource_types or [])

        # 统一预算模型：只依据意图强度、查询复杂度和类型数量，不做主题/资源类型硬编码特判。
        intent_boost = min(260, max_priority * 20)
        complexity_boost = 80 if query_len >= 20 else 40 if query_len >= 10 else 0
        multi_intent_boost = min(120, high_priority_count * 60)
        multi_type_boost = 40 if type_count >= 2 else 0

        adjusted_count = base_count + intent_boost + complexity_boost + multi_intent_boost + multi_type_boost
        adjusted_count = max(120, min(420, adjusted_count))
        print(
            "   📦 统一检索预算: "
            f"base={base_count}, priority={max_priority}, high_intents={high_priority_count}, "
            f"query_len={query_len}, type_count={type_count}, final={adjusted_count}"
        )
        return adjusted_count
