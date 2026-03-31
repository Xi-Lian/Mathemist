from .._shared import *


class _ExtractDifficultyInfoMixin:
    def _extract_difficulty_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 从用户输入中提取难度信息
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            难度信息字典
        """
        for difficulty, keywords in self.V33_DIFFICULTY_PATTERNS.items():
            for keyword in keywords:
                if keyword in user_input:
                    return {
                        "difficulty": difficulty,
                        "difficulty_keywords_matched": keyword
                    }
        return None
