from .._shared import *


class _DetermineDomainMixin:
    def _determine_domain(self, core_theme: Optional[str], related_themes: List[str], lesson_title: str, lesson_content: str) -> str:
        """
        根据核心主题和相关主题确定领域
        
        优先级：
        1. 核心主题对应的领域
        2. 相关主题中最相关的领域
        3. 标题和内容分析
        4. 默认领域（其他）
        """
        # 1. 核心主题对应的领域
        if core_theme:
            domain = self.theme_domain_map.get(core_theme)
            if domain:
                return domain
        
        # 2. 相关主题中最相关的领域
        for theme in related_themes:
            domain = self.theme_domain_map.get(theme)
            if domain:
                return domain
        
        # 3. 标题和内容分析
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # 检查三角函数相关
        if any(keyword in full_text for keyword in ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]):
            return "三角函数"
        
        # 检查具体函数相关
        if any(keyword in full_text for keyword in ["指数函数", "对数函数", "幂函数"]):
            return "具体函数"
        
        # 检查一般函数相关
        if any(keyword in full_text for keyword in ["函数的概念", "函数的表示法", "函数的性质", "单调性", "奇偶性", "周期性"]):
            return "一般函数"
        
        # 4. 默认领域
        return "其他"
