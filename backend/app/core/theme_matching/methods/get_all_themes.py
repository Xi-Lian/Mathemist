from .._shared import *


class _GetAllThemesMixin:
    def get_all_themes(self) -> List[str]:
        """
        获取所有支持的主题列表
        
        Returns:
            主题列表
        """
        return list(self.THEME_KEYWORD_MAP.keys())
