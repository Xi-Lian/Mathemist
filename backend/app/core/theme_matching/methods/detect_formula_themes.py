from .._shared import *


class _DetectFormulaThemesMixin:
    def _detect_formula_themes(self, content: str) -> List[Dict[str, Any]]:
        """
        基于公式的主题检测
        """
        formula_themes = []
        
        # 幂函数: y = x^a
        if re.search(r'y\s*=\s*x\s*\^\s*[a-zA-Z]', content):
            formula_themes.append({
                "theme": "幂函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = x^a"]
            })
        
        # 指数函数: y = a^x
        if re.search(r'y\s*=\s*[a-zA-Z]\s*\^\s*x', content):
            formula_themes.append({
                "theme": "指数函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = a^x"]
            })
        
        # 二次函数: y = ax² + bx + c
        if re.search(r'y\s*=\s*[a-zA-Z]\s*[xX]\s*[\^2²]', content):
            formula_themes.append({
                "theme": "二次函数",
                "confidence": 0.85,
                "evidence": "formula",
                "matched_keywords": ["y = ax²"]
            })
        
        # 三角函数
        if re.search(r'[sS][iI][nN]|cos|tan|sin|cos|tan', content):
            formula_themes.append({
                "theme": "三角函数",
                "confidence": 0.75,
                "evidence": "formula",
                "matched_keywords": ["sin", "cos", "tan"]
            })
        
        return formula_themes
