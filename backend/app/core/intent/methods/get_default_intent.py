from .._shared import *


class _GetDefaultIntentMixin:
    def _get_default_intent(self, error_msg: str = None, user_needs: str = "", resource_types: List[str] = None) -> Dict[str, Any]:
        """
        获取默认意图结果
        
        Args:
            error_msg: 错误信息
            user_needs: 用户需求描述
            resource_types: 资源类型列表
        
        Returns:
            意图结果
        """
        if resource_types is None:
            resource_types = []
        
        return {
            "intent": self.INTENT_SEARCH,
            "user_needs": user_needs,
            "resource_types": resource_types,
            "intents": [
                {"type": self.INTENT_SEARCH, "confidence": 0.9},
                {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
