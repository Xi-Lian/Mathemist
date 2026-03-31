from .._shared import *


class _ExtractCoreConceptsMixin:
    def _extract_core_concepts(self, query: str) -> List[str]:
        """
        提取核心概念
        """
        concepts = []
        
        for concept, terms in self.math_keywords.items():
            for term in terms:
                if term in query and concept not in concepts:
                    concepts.append(concept)
                    break
        
        return concepts
