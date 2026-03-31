from .._shared import *


class _IsDownwardRecommendationMixin:
    def _is_downward_recommendation(self, theme: str, lesson_title: str, lesson_content: str) -> bool:
        """
        V9.2：判断是否为向下推荐（父→子）
        
        向下推荐：用户查询父主题，推荐子主题（更具体的内容）
        向上推荐：用户查询子主题，推荐父主题（更泛化的内容）
        """
        # 提取教案的主题
        lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
        
        if not lesson_theme:
            return True  # 无法确定，默认允许
        
        # 检查是否为父子关系
        for parent_theme, child_themes in self.theme_hierarchy.items():
            if theme == parent_theme and lesson_theme in child_themes:
                # 向下推荐：父主题查询，子主题教案
                return True
            elif theme in child_themes and lesson_theme == parent_theme:
                # 向上推荐：子主题查询，父主题教案
                return False
        
        # 不是父子关系，默认允许
        return True
