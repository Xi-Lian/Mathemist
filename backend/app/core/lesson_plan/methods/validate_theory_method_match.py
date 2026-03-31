from .._shared import *


class _ValidateTheoryMethodMatchMixin:
    def _validate_theory_method_match(self, lesson_plan: str, teaching_method: str) -> str:
        """
        验证理论选择是否与教学方法匹配
        
        Args:
            lesson_plan: 教案文本
            teaching_method: 教学方法
        
        Returns:
            验证后的教案文本
        """
        import re
        
        # 扩展关键环节列表，确保更多环节的理论匹配
        key_sections = [
            "知识与技能目标", "过程与方法目标", "情感态度与价值观目标",
            "教学方法", "教师引导", "自主探究", "小组合作",
            "典型例题", "基础训练", "解题思路"
        ]
        
        for section in key_sections:
            # 提取该环节的理论引用
            section_pattern = rf"###.*?{re.escape(section)}.*?📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
            match = re.search(section_pattern, lesson_plan, re.DOTALL)
            
            if match:
                card_key = match.group(1)
                theory_name = match.group(2)
                
                # 检查理论是否适合当前教学方法
                if not self._is_theory_suitable_for_method(card_key, teaching_method):
                    print(f"⚠️ 发现 {section} 环节的理论选择与教学方法不匹配: {theory_name}")
                    # 推荐更适合的理论
                    recommended_theories = self._get_dynamic_recommended_theories(section, teaching_method)
                    for recommended_key in recommended_theories:
                        if recommended_key in self.theory_cards_index:
                            recommended_info = self.theory_cards_index[recommended_key]
                            recommended_name = recommended_info["name"]
                            core_view = recommended_info["core_view"]
                            
                            # 替换理论引用
                            old_ref = f"[{card_key}：{theory_name}]"
                            new_ref = f"[{recommended_key}：{recommended_name}]"
                            lesson_plan = lesson_plan.replace(old_ref, new_ref)
                            
                            # 更新理论依据内容
                            old_content_pattern = rf"\*\*📌 理论依据：\[{card_key}：{re.escape(theory_name)}\] - .*? - 应用场景：.*?\*\*"
                            new_content = f"**📌 理论依据：[{recommended_key}：{recommended_name}] - {core_view} - 应用场景：指导{section}环节的教学设计，体现了{recommended_name}的应用价值**"
                            lesson_plan = re.sub(old_content_pattern, new_content, lesson_plan, flags=re.DOTALL)
                            
                            print(f"✅ 替换为更适合的理论: {recommended_key}：{recommended_name}")
                            break
        
        return lesson_plan
