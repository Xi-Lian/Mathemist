from .._shared import *


class _ExtractLessonThemeMixin:
    def _extract_lesson_theme(self, lesson_title: str, lesson_content: str) -> Optional[str]:
        """
        V9.1：从教案中提取主题
        
        用于计算领域距离
        """
        # 尝试从标题中提取主题
        title_lower = lesson_title.lower()
        
        # 检查常见主题
        # V24.4改进：添加一次函数
        common_themes = [
            "指数函数", "对数函数", "幂函数", "三角函数", "二次函数", "一次函数",
            "函数的概念", "函数的单调性", "函数的奇偶性", "函数的周期性"
        ]
        
        for theme in common_themes:
            if theme in title_lower:
                return theme
        
        # 如果标题中没有，尝试从内容中提取
        content_lower = lesson_content.lower()
        for theme in common_themes:
            if theme in content_lower:
                return theme
        
        return None
