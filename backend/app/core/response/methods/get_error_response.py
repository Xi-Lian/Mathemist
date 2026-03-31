from .._shared import *


class _GetErrorResponseMixin:
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"抱歉，响应生成过程中出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
