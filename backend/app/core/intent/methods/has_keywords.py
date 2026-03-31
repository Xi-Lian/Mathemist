from .._shared import *


class _HasKeywordsMixin:
    def _has_keywords(self, text: str, intent_type: str) -> bool:
        """
        检查文本是否包含指定意图的关键词
        
        Args:
            text: 输入文本
            intent_type: 意图类型
        
        Returns:
            是否包含关键词
        """
        keywords = self.KEYWORDS.get(intent_type, [])
        return any(keyword in text for keyword in keywords)
