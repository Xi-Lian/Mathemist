from .._shared import *


class _IsTheorySuitableForMethodMixin:
    def _is_theory_suitable_for_method(self, card_key_or_info: str or Dict[str, str], teaching_method: str) -> bool:
        """
        动态检查理论是否适合当前教学方法（基于理论卡片内容的关键词分析）
        
        Args:
            card_key_or_info: 理论卡片键或理论卡片信息
            teaching_method: 教学方法
        
        Returns:
            是否适合
        """
        # 获取理论卡片信息
        if isinstance(card_key_or_info, str):
            card_info = self.theory_cards_index.get(card_key_or_info, {})
        else:
            card_info = card_key_or_info
        
        applicable_methods = card_info.get('applicable_methods', '')
        theory_name = card_info.get('name', '')
        core_view = card_info.get('core_view', '')
        teaching_inspiration = card_info.get('teaching_inspiration', '')
        
        # 组合理论的所有文本内容
        combined_theory_text = theory_name + " " + core_view + " " + teaching_inspiration
        
        # 特殊处理：多元智能理论适合所有教学方法
        if '多元智能' in theory_name:
            return True
        
        if '所有教学方法' in applicable_methods:
            return True
        
        # 检查教学方法是否匹配
        if teaching_method in applicable_methods:
            return True
        
        # 定义教学方法关键词
        method_keywords = {
            '讲授式教学': ['讲授', '讲解', '传递', '灌输', '呈现', '示范', '演示', '教师主导', '知识传递'],
            '探究式教学': ['探究', '发现', '探索', '研究', '实验', '调查', '自主', '建构', '学生自主'],
            '合作学习': ['合作', '协作', '小组', '团队', '同伴', '互动', '交流', '协作'],
            '自主学习': ['自主', '独立', '自我', '元认知', '监控', '反思', '自我调节'],
            '翻转课堂': ['翻转', '课前', '课后', '预习', '复习', '自主学习'],
            '项目式学习': ['项目', '实践', '应用', '综合', '真实情境', '实际问题'],
            '混合式教学': ['混合', '多种', '多元', '综合', '多样化']
        }
        
        # 动态检查教学方法匹配（基于关键词分析）
        for method_key, keywords in method_keywords.items():
            if method_key in teaching_method:
                # 检查理论内容中是否包含该教学方法的关键词
                for keyword in keywords:
                    if keyword in combined_theory_text:
                        return True
        
        return False
