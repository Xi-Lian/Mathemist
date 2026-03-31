from .._shared import *


class _UpdateContextHistoryMixin:
    def _update_context_history(self, user_input: str, result: Dict[str, Any]) -> None:
        """
        更新上下文历史
        
        Args:
            user_input: 用户输入
            result: 分析结果
        """
        context_entry = {
            "user_input": user_input,
            "intent": result.get("intent"),
            "clarified_topic": result.get("clarified_topic"),
            "resource_types": result.get("resource_types"),
            "timestamp": "2026-03-15"  # 实际应用中应使用当前时间
        }
        
        self.context_history.append(context_entry)
        # 保持历史记录不超过10条
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
