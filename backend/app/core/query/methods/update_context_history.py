from .._shared import *


class _UpdateContextHistoryMixin:
    def _update_context_history(self, query: str, result: Dict[str, Any]) -> None:
        """
        V33.0改进：更新上下文历史
        
        Args:
            query: 原始查询
            result: 预处理结果
        """
        context_entry = {
            "original_query": query,
            "cleaned_query": result.get("cleaned_query", ""),
            "core_concepts": result.get("core_concepts", []),
            "intent": result.get("intent", {}),
            "timestamp": "2026-03-16"  # 实际应用中应使用当前时间
        }
        
        self.context_history.append(context_entry)
        # 保持历史记录不超过5条
        if len(self.context_history) > 5:
            self.context_history = self.context_history[-5:]
