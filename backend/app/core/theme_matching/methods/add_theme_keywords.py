from .._shared import *


class _AddThemeKeywordsMixin:
    def add_theme_keywords(self, theme: str, keywords: List[str], keyword_type: str = "related") -> bool:
        """
        动态添加主题关键词
        
        Args:
            theme: 主题名
            keywords: 关键词列表
            keyword_type: 关键词类型 (core/related/chapter/path)
        
        Returns:
            是否成功
        """
        if theme not in self.THEME_KEYWORD_MAP:
            return False
        
        type_map = {
            "core": "core_keywords",
            "related": "related_keywords",
            "chapter": "chapter_indicators",
            "path": "path_keywords"
        }
        
        key = type_map.get(keyword_type)
        if not key:
            return False
        
        for kw in keywords:
            if kw not in self.THEME_KEYWORD_MAP[theme][key]:
                self.THEME_KEYWORD_MAP[theme][key].append(kw)
        
        return True
