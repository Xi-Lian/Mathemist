from .._shared import *


class _CountKeywordMatchesMixin:
    def _count_keyword_matches(self, keywords: List[str], text: str) -> int:
        """计算关键词在文本中的匹配次数"""
        if not text:
            return 0
        
        text_lower = text.lower()
        count = 0
        for keyword in keywords:
            count += text_lower.count(keyword.lower())
        return count
