from .._shared import *


class _CleanLatexExpressionMixin:
    def _clean_latex_expression(self, expr: str) -> str:
        """
        清理LaTeX表达式，提取关键数学信息
        """
        if not expr:
            return ""
        
        cleaned = re.sub(r'\s+', '', expr.strip())
        cleaned = re.sub(r'\\left|\\right', '', cleaned)
        cleaned = re.sub(r'\\frac', '/', cleaned)
        cleaned = re.sub(r'\\cdot', '*', cleaned)
        cleaned = re.sub(r'\\times', '*', cleaned)
        cleaned = re.sub(r'\\div', '/', cleaned)
        cleaned = re.sub(r'\\pm', '±', cleaned)
        cleaned = re.sub(r'\\neq', '≠', cleaned)
        cleaned = re.sub(r'\\leq', '≤', cleaned)
        cleaned = re.sub(r'\\geq', '≥', cleaned)
        cleaned = re.sub(r'\\infty', '∞', cleaned)
        cleaned = re.sub(r'\\alpha', 'α', cleaned)
        cleaned = re.sub(r'\\beta', 'β', cleaned)
        cleaned = re.sub(r'\\gamma', 'γ', cleaned)
        cleaned = re.sub(r'\\delta', 'δ', cleaned)
        cleaned = re.sub(r'\\theta', 'θ', cleaned)
        cleaned = re.sub(r'\\pi', 'π', cleaned)
        cleaned = re.sub(r'\\sin', 'sin', cleaned)
        cleaned = re.sub(r'\\cos', 'cos', cleaned)
        cleaned = re.sub(r'\\tan', 'tan', cleaned)
        cleaned = re.sub(r'\\log', 'log', cleaned)
        cleaned = re.sub(r'\\ln', 'ln', cleaned)
        cleaned = re.sub(r'\\sqrt', '√', cleaned)
        cleaned = re.sub(r'\\sum', '∑', cleaned)
        cleaned = re.sub(r'\\int', '∫', cleaned)
        cleaned = re.sub(r'\\lim', 'lim', cleaned)
        cleaned = cleaned.replace('{', '').replace('}', '')
        
        return cleaned
