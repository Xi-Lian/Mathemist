from .._shared import *


class _GenerateSearchVersionsMixin:
    def _generate_search_versions(self, preprocess_result: Dict[str, Any]) -> List[str]:
        """
        生成多种检索版本
        """
        versions = []
        
        original = preprocess_result["original_query"]
        cleaned = preprocess_result["cleaned_query"]
        keywords = preprocess_result["keywords"]
        concepts = preprocess_result["core_concepts"]
        latex = preprocess_result["latex_expressions"]
        
        if original:
            versions.append(original)
        
        if cleaned and cleaned != original:
            versions.append(cleaned)
        
        if keywords:
            versions.append(" ".join(keywords))
        
        if concepts:
            versions.append(" ".join(concepts))
        
        if keywords and concepts:
            versions.append(" ".join(keywords + concepts))
        
        if latex:
            versions.append(" ".join(latex))
        
        if keywords and latex:
            versions.append(" ".join(keywords + latex))
        
        unique_versions = []
        seen = set()
        for v in versions:
            if v and v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        return unique_versions[:8]
