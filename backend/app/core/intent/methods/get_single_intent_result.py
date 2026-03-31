from .._shared import *


class _GetSingleIntentResultMixin:
    def _get_single_intent_result(
        self, 
        primary_intent: str, 
        error_msg: str = None,
        user_needs: str = "",
        resource_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取单一意图结果
        
        Args:
            primary_intent: 主要意图
            error_msg: 错误信息
            user_needs: 用户需求描述
            resource_types: 资源类型列表
        
        Returns:
            意图结果
        """
        if resource_types is None:
            resource_types = []
        
        return {
            "intent": primary_intent,
            "user_needs": user_needs,
            "resource_types": resource_types,
            "intents": [
                {"type": primary_intent, "confidence": 0.9},
                {"type": self.INTENT_SEARCH, "confidence": 0.1},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
