from .._shared import *


class _CheckKeywordsInTextMixin:
    def _check_keywords_in_text(self, text: str, keywords: List[str]) -> bool:
        """
        检查文本中是否包含任意关键词
        
        Args:
            text: 待检查文本
            keywords: 关键词列表
        
        Returns:
            是否匹配
        """
        if not text:
            return False
        text_lower = text.lower()
        for keyword in keywords:
            if keyword.lower() in text_lower:
                return True
        return False
