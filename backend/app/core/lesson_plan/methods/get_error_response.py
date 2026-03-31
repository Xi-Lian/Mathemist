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
        return f"""
# ❌ 教案生成失败

抱歉，教案生成过程中出现错误：**{error_msg}**

## 可能的原因：
1. 网络连接问题，无法访问AI模型
2. API密钥配置错误
3. 理论资源或教案示例加载失败

## 建议解决方案：
1. 检查网络连接
2. 确认.env文件中的API密钥配置正确
3. 稍后重试或联系管理员

---
"""
