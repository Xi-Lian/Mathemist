from .._shared import *


class _DynamicThemeDetectionMixin:
    def dynamic_theme_detection(self, content: str, title: str = "") -> List[Dict[str, Any]]:
        """
        动态主题检测
        
        Args:
            content: 资源内容
            title: 资源标题
        
        Returns:
            检测到的主题列表
        """
        detected_themes = []
        
        # 1. 基于主题关键词映射的检测
        for theme, config in self.THEME_KEYWORD_MAP.items():
            # 检查核心关键词
            if self._check_keywords_in_text(content, config["core_keywords"]) or \
               self._check_keywords_in_text(title, config["core_keywords"]):
                detected_themes.append({
                    "theme": theme,
                    "confidence": 0.9,
                    "evidence": "core_keyword",
                    "matched_keywords": [kw for kw in config["core_keywords"] 
                                        if kw in content or kw in title]
                })
            # 检查相关关键词
            elif self._check_keywords_in_text(content, config["related_keywords"]) or \
                 self._check_keywords_in_text(title, config["related_keywords"]):
                detected_themes.append({
                    "theme": theme,
                    "confidence": 0.7,
                    "evidence": "related_keyword",
                    "matched_keywords": [kw for kw in config["related_keywords"] 
                                        if kw in content or kw in title]
                })
        
        # 2. 基于数学公式的动态检测
        formula_themes = self._detect_formula_themes(content)
        detected_themes.extend(formula_themes)
        
        # 3. 基于上下文的动态检测
        context_themes = self._detect_context_themes(content, title)
        detected_themes.extend(context_themes)
        
        # 4. 去重并按置信度排序
        unique_themes = {}
        for theme_info in detected_themes:
            theme = theme_info["theme"]
            if theme not in unique_themes or theme_info["confidence"] > unique_themes[theme]["confidence"]:
                unique_themes[theme] = theme_info
        
        return sorted(unique_themes.values(), key=lambda x: -x["confidence"])
