from .._shared import *


class _ExtractCompleteThemeMixin:
    def _extract_complete_theme(self, query: str) -> str:
        """
        提取完整主题
        
        Args:
            query: 查询文本
            
        Returns:
            完整主题字符串
        """
        # 按长度降序排序，优先匹配更长的主题
        sorted_themes = sorted(self.complete_themes, key=len, reverse=True)
        
        for theme in sorted_themes:
            if theme in query:
                logger.info(f"识别到完整主题: {theme}")
                return theme
        
        # 如果没有识别到完整主题，返回空
        return ""
