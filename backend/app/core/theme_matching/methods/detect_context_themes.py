from .._shared import *


class _DetectContextThemesMixin:
    def _detect_context_themes(self, content: str, title: str) -> List[Dict[str, Any]]:
        """
        基于上下文的主题检测
        """
        context_themes = []
        
        # 基于教学目标
        if any(keyword in content for keyword in ["教学目标", "学习目标", "教学重难点"]):
            # 分析教学目标中的主题
            lines = content.split('\n')
            for line in lines:
                if "目标" in line or "重点" in line:
                    for theme in self.THEME_KEYWORD_MAP:
                        if theme in line:
                            context_themes.append({
                                "theme": theme,
                                "confidence": 0.7,
                                "evidence": "teaching_goal",
                                "matched_keywords": [theme]
                            })
        
        # 基于章节信息
        chapter_patterns = [r'第[一二三四五六七八九十]+章', r'第[0-9]+章', r'模块[0-9]+']
        for pattern in chapter_patterns:
            match = re.search(pattern, content + title)
            if match:
                chapter = match.group()
                # 映射章节到主题
                chapter_theme_map = {
                    "第三章": ["函数的概念", "函数的性质", "二次函数", "幂函数"],
                    "第四章": ["指数函数", "对数函数"],
                    "第五章": ["三角函数"],
                    "第六章": ["三角恒等变换"]
                }
                for chapter_key, themes in chapter_theme_map.items():
                    if chapter_key in chapter:
                        for theme in themes:
                            context_themes.append({
                                "theme": theme,
                                "confidence": 0.6,
                                "evidence": "chapter",
                                "matched_keywords": [chapter]
                            })
        
        return context_themes
