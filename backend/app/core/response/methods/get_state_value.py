from .._shared import *


class _GetStateValueMixin:
    def _get_state_value(self, state: Any, key: str, default: Any = None) -> Any:
        """
        从状态对象中获取值（支持 MathAgentState 对象和字典）
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
            key: 键名
            default: 默认值
        
        Returns:
            对应的值
        """
        if hasattr(state, key):
            return getattr(state, key)
        elif isinstance(state, dict):
            return state.get(key, default)
        else:
            return default


# 向后兼容的函数接口
