from .._shared import *


class _GenerateSummaryMixin:
    def _generate_summary(self, content: str, max_length: int = 200) -> str:
        """生成内容摘要"""
        # 移除markdown标记和多余空白
        content = re.sub(r'[#*|`\[\]]', '', content)
        content = re.sub(r'\s+', '', content)
        
        # 返回前max_length个字符
        return content[:max_length] if len(content) > max_length else content
