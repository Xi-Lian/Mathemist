from .._shared import *


class _ExpandQueryWithSynonymsMixin:
    def expand_query_with_synonyms(self, query: str) -> List[str]:
        """
        使用同义词扩展查询
        """
        expanded_queries = [query]
        
        for term, synonyms in self.math_synonyms.items():
            if term in query:
                for syn in synonyms:
                    if syn != term:
                        expanded = query.replace(term, syn)
                        if expanded not in expanded_queries:
                            expanded_queries.append(expanded)
        
        return expanded_queries
