from .._shared import *


class _CheckKeywordsMixin:
    def _check_keywords(self, content: str, keywords: List[str]) -> bool:
        """检查内容中是否包含关键词"""
        content_lower = content.lower()
        for keyword in keywords:
            if keyword.lower() in content_lower:
                return True
        return False
