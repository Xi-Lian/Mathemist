from .._shared import *


class _ExtractKeywordsFromTextMixin:
    def _extract_keywords_from_text(self, text: str, keyword_list: List[str]) -> List[str]:
        """
        V54.0改进：从文本中提取匹配的关键词
        
        Args:
            text: 待提取的文本
            keyword_list: 关键词列表
            
        Returns:
            匹配到的关键词列表
        """
        matched_keywords = []
        text_lower = text.lower()
        
        for keyword in keyword_list:
            if keyword.lower() in text_lower:
                matched_keywords.append(keyword)
        
        return matched_keywords
