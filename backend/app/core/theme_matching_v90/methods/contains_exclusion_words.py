from .._shared import *


class _ContainsExclusionWordsMixin:
    def _contains_exclusion_words(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.2：检查文本中是否包含主题的排除词
        
        注意：此方法已被 _calculate_exclusion_factor 替代
        """
        return False
