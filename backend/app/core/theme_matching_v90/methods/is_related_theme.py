from .._shared import *


class _IsRelatedThemeMixin:
    def _is_related_theme(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.1：检查主题是否与教案内容相关（基于主题层级关系）
        
        改进：区分推荐方向
        - 向下推荐（父→子）：允许
        - 向上推荐（子→父）：需要额外检查
        """
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # 检查主题是否在层级关系中
        for parent_theme, child_themes in self.theme_hierarchy.items():
            if theme == parent_theme:
                # 检查是否包含子主题（向下推荐）
                for child_theme in child_themes:
                    if child_theme.lower() in full_text:
                        return True
            elif theme in child_themes:
                # 检查是否包含父主题（向上推荐）
                if parent_theme.lower() in full_text:
                    return True
        
        return False
