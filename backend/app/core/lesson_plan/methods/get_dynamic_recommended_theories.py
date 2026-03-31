from .._shared import *


class _GetDynamicRecommendedTheoriesMixin:
    def _get_dynamic_recommended_theories(self, section: str, teaching_method: str, content_type: str = "概念教学", used_theories: List[str] = None) -> List[str]:
        """
        根据教学环节、教学方法和内容类型动态推荐理论
        
        Args:
            section: 教学环节
            teaching_method: 教学方法
            content_type: 内容类型
            used_theories: 已使用的理论列表，用于增加理论多样性
        
        Returns:
            推荐的理论卡片列表
        """
        recommended_theories = []
        
        # 遍历所有理论卡片，根据匹配度排序
        theory_scores = {}
        
        for card_key, card_info in self.theory_cards_index.items():
            # 如果该理论已经被使用，降低其优先级
            if used_theories and card_key in used_theories:
                continue
            
            score = 0
            
            # 检查教学环节匹配
            applicable_links = card_info.get('applicable_links', '')
            if section in applicable_links:
                score += 4
            elif '所有环节' in applicable_links:
                score += 2
            elif any(keyword in section for keyword in ['导入', '讲解', '练习', '总结', '作业', '探究', '合作', '自主']):
                score += 1
            
            # 检查教学方法匹配
            applicable_methods = card_info.get('applicable_methods', '')
            if self._is_theory_suitable_for_method(card_info, teaching_method):
                score += 5  # 提高教学方法匹配权重
            elif '所有教学方法' in applicable_methods:
                score += 2
            
            # 检查内容类型匹配
            applicable_content = card_info.get('applicable_content', '')
            if content_type in applicable_content:
                score += 3
            elif '所有内容类型' in applicable_content:
                score += 1
            
            # 检查教学启发要素丰富度
            teaching_inspiration_elements = card_info.get('teaching_inspiration_elements', [])
            if len(teaching_inspiration_elements) > 0:
                score += 1
            if len(teaching_inspiration_elements) > 2:
                score += 1
            
            # 根据环节类型动态调整理论偏好（基于教学启发和核心观点的关键词分析）
            section_preferences_keywords = {
                '知识与技能目标': ['技能', '目标', '行为', '掌握', '训练', '强化', '练习'],
                '过程与方法目标': ['过程', '方法', '探究', '建构', '发现', '自主', '合作'],
                '情感态度与价值观目标': ['情感', '态度', '价值观', '动机', '兴趣', '价值', '认同', '态度'],
                '教学重点': ['重点', '核心', '关键', '重要', '主要'],
                '教学难点': ['难点', '困难', '困难', '障碍', '挑战'],
                '教学方法': ['方法', '策略', '方式', '手段', '途径'],
                '创设情境': ['情境', '真实', '生活', '实际', '问题', '情境'],
                '提出问题': ['问题', '提问', '启发', '引导', '探究'],
                '激发兴趣': ['兴趣', '动机', '激发', '吸引', '好奇', '兴趣'],
                '自主探究': ['自主', '探究', '探索', '发现', '研究'],
                '小组合作': ['合作', '小组', '协作', '团队', '同伴'],
                '教师引导': ['引导', '支架', '支持', '帮助', '脚手架'],
                '典型例题': ['例题', '典型', '示范', '例子', '案例'],
                '解题思路': ['思路', '方法', '策略', '技巧', '解题'],
                '易错点辨析': ['易错', '错误', '辨析', '注意', '陷阱'],
                '基础训练': ['基础', '训练', '练习', '巩固', '强化'],
                '综合应用': ['综合', '应用', '实践', '运用', '解决'],
                '分层作业': ['分层', '差异', '个性化', '不同', '层次'],
                '知识梳理': ['梳理', '总结', '归纳', '整理', '系统'],
                '方法提炼': ['方法', '提炼', '总结', '思想', '策略'],
                '反思评价': ['反思', '评价', '评估', '反馈', '元认知']
            }
            
            # 根据环节偏好动态调整分数
            theory_name = card_info.get('name', '')
            core_view = card_info.get('core_view', '')
            teaching_inspiration = card_info.get('teaching_inspiration', '')
            
            # 组合理论的所有文本内容
            combined_theory_text = theory_name + " " + core_view + " " + teaching_inspiration
            
            if section in section_preferences_keywords:
                keywords = section_preferences_keywords[section]
                # 计算匹配的关键词数量
                matched_keywords = sum(1 for keyword in keywords if keyword in combined_theory_text)
                # 根据匹配的关键词数量加分
                if matched_keywords > 0:
                    score += matched_keywords * 0.5
            
            if score > 0:
                theory_scores[card_key] = score
        
        # 按分数排序，返回前5个理论（增加理论多样性）
        sorted_theories = sorted(theory_scores.items(), key=lambda x: x[1], reverse=True)
        recommended_theories = [theory[0] for theory in sorted_theories[:5]]
        
        # 确保至少有一个理论
        if not recommended_theories:
            # 如果没有匹配的理论，返回所有理论卡片中的前5个
            all_theories = list(self.theory_cards_index.keys())
            recommended_theories = all_theories[:5]
        
        return recommended_theories
