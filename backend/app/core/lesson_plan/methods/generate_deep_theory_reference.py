from .._shared import *


class _GenerateDeepTheoryReferenceMixin:
    def _generate_deep_theory_reference(self, card_key: str, section: str, teaching_method: str) -> str:
        """
        生成深度理论引用，体现教学启发
        
        Args:
            card_key: 理论卡片键
            section: 教学环节
            teaching_method: 教学方法
        
        Returns:
            深度理论引用
        """
        theory_info = self.theory_cards_index.get(card_key, {})
        theory_name = theory_info.get('name', '未知理论')
        core_view = theory_info.get('core_view', '未知核心观点')
        teaching_inspiration = theory_info.get('teaching_inspiration', '')
        teaching_inspiration_elements = theory_info.get('teaching_inspiration_elements', [])
        
        # 构建深度理论引用
        reference_parts = [
            f"{card_key}：{theory_name}",
            f"核心观点：{core_view}"
        ]
        
        # 添加教学启发信息
        if teaching_inspiration:
            reference_parts.append(f"教学启发：{teaching_inspiration}")
        
        # 添加教学启发要素应用
        if teaching_inspiration_elements:
            application_info = "设计体现了教学启发中的：" + "、".join(teaching_inspiration_elements)
            reference_parts.append(f"应用场景：{application_info}")
        else:
            reference_parts.append("应用场景：详细说明该理论如何指导本环节设计")
        
        return " - ".join(reference_parts)
