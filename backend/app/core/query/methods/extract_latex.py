from .._shared import *


class _ExtractLatexMixin:
    def _extract_latex(self, query: str) -> List[str]:
        """
        提取LaTeX表达式
        """
        latex_expressions = []
        latex_expressions.extend(re.findall(r'\$(.*?)\$', query))
        latex_expressions.extend(re.findall(r'\\\((.*?)\\\)', query))
        latex_expressions.extend(re.findall(r'\\\[(.*?)\\\]', query))
        
        cleaned_expressions = []
        for expr in latex_expressions:
            cleaned = self._clean_latex_expression(expr)
            if cleaned:
                cleaned_expressions.append(cleaned)
        
        return cleaned_expressions
