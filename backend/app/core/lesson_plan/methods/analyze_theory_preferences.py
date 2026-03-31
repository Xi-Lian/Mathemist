from .._shared import *


class _AnalyzeTheoryPreferencesMixin:
    def _analyze_theory_preferences(self, user_input: str) -> List[str]:
        """
        分析用户输入中的理论偏好
        
        Args:
            user_input: 用户需求
        
        Returns:
            理论偏好列表
        """
        theory_preferences = []
        
        # 定义理论关键词
        theories = {
            "建构主义": ["建构主义", "建构"],
            "行为主义": ["行为主义", "行为"],
            "认知主义": ["认知主义", "认知"],
            "合作学习": ["合作学习", "合作"],
            "探究学习": ["探究学习", "探究"]
        }
        
        # 匹配理论偏好
        for theory, keywords in theories.items():
            for keyword in keywords:
                if keyword in user_input:
                    theory_preferences.append(theory)
                    break
        
        return theory_preferences
