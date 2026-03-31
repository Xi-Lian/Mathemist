from .._shared import *


class _EnhanceTheoryCardParsingMixin:
    def _enhance_theory_card_parsing(self, theory_index: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, str]]:
        """
        增强理论卡片解析，提取教学启发要素
        
        Args:
            theory_index: 理论卡片索引
        
        Returns:
            增强后的理论卡片索引
        """
        import re
        
        for card_key, card_info in theory_index.items():
            # 提取教学启发要素
            teaching_inspiration = card_info.get('teaching_inspiration', '')
            teaching_inspiration_elements = []
            
            if teaching_inspiration:
                # 尝试从教学启发中提取具体要素
                elements = re.split(r'[，。；]', teaching_inspiration)
                for element in elements:
                    element = element.strip()
                    if element:
                        teaching_inspiration_elements.append(element)
            
            # 添加教学启发要素到理论卡片信息
            card_info['teaching_inspiration_elements'] = teaching_inspiration_elements
        
        return theory_index
