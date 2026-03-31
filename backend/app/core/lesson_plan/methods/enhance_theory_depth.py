from .._shared import *


class _EnhanceTheoryDepthMixin:
    def _enhance_theory_depth(self, card_key: str, section: str, teaching_method: str) -> str:
        """
        动态增强理论引用深度，确保体现理论核心要素（基于理论卡片内容的关键词分析）
        
        Args:
            card_key: 理论卡片键
            section: 教学环节
            teaching_method: 教学方法
        
        Returns:
            增强深度后的理论依据描述
        """
        theory_info = self.theory_cards_index.get(card_key, {})
        theory_name = theory_info.get('name', '未知理论')
        core_view = theory_info.get('core_view', '未知核心观点')
        teaching_inspiration = theory_info.get('teaching_inspiration', '')
        teaching_inspiration_elements = theory_info.get('teaching_inspiration_elements', [])
        
        # 如果有教学启发要素，直接返回核心观点和教学启发
        if teaching_inspiration_elements:
            elements_str = "、".join(teaching_inspiration_elements)
            return f"{core_view} - 教学启发：{teaching_inspiration} - 体现要素：{elements_str}"
        
        # 如果没有教学启发要素，返回核心观点
        return core_view
