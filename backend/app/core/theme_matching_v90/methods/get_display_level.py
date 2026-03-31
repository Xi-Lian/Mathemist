from .._shared import *


class _GetDisplayLevelMixin:
    def _get_display_level(self, score: float) -> str:
        """
        V9.2：根据分数确定展示级别
        
        Args:
            score: 相关性分数
        
        Returns:
            str: 展示级别 (core/related/extended/candidate)
        """
        if score >= self.display_levels["core"]["min_score"]:
            return "core"
        elif score >= self.display_levels["related"]["min_score"]:
            return "related"
        elif score >= self.display_levels["extended"]["min_score"]:
            return "extended"
        elif score >= self.display_levels["candidate"]["min_score"]:
            return "candidate"
        else:
            return "none"
