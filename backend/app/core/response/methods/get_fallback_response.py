from .._shared import *


class _GetFallbackResponseMixin:
    def _get_fallback_response(self, state: Any) -> str:
        """
        V33.0改进：获取降级响应（当完整响应生成失败时）
        
        Args:
            state: 状态对象
        
        Returns:
            降级响应文本
        """
        # 尝试获取已有的部分响应
        existing_response = self._get_state_value(state, "response", "")
        if existing_response:
            return f"系统响应生成不完整，以下是部分结果：\n\n{existing_response}"
        
        # 尝试获取检索到的资源
        retrieved_resources = self._get_state_value(state, "retrieved_resources", {})
        if retrieved_resources:
            return """系统响应生成不完整，但已找到相关资源。

请尝试：
- 刷新页面重新加载
- 使用更简单的查询方式
- 稍后重试"""
        
        return """抱歉，系统响应生成失败。

请尝试：
- 刷新页面重新加载
- 使用更简单的查询方式
- 稍后重试
- 联系管理员"""
