from .._shared import *


class _ExtractKeywordsMixin:
    def _extract_keywords(self, query: str) -> List[str]:
        """
        提取关键词
        """
        keywords = []
        
        for concept, terms in self.math_keywords.items():
            for term in terms:
                if term in query and term not in keywords:
                    keywords.append(term)
        
        if not keywords:
            words = re.findall(r'[\u4e00-\u9fff]{2,4}', query)
            keywords = words[:5]
        
        return keywords
