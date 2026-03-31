from .._shared import *


class _CalculateDirectionFactorMixin:
    def _calculate_direction_factor(self, theme: str, lesson_title: str, lesson_content: str) -> float:
        """
        V9.2：计算方向控制因子
        
        向下推荐（父→子）：1.0
        向上推荐（子→父）：0.6
        其他：1.0
        
        Returns:
            float: 方向控制因子 (0.6-1.0)
        """
        if self._is_downward_recommendation(theme, lesson_title, lesson_content):
            return 1.0  # 向下推荐，不降低分数
        else:
            return 0.6  # 向上推荐，适度降低分数
