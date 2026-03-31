from .._shared import *


class _EvaluateTheoryQualityMixin:
    def _evaluate_theory_quality(self, lesson_plan: str, teaching_method: str, content_type: str) -> str:
        """
        理论引用质量三维评估
        
        Args:
            lesson_plan: 教案文本
            teaching_method: 教学方法
            content_type: 教学内容类型
        
        Returns:
            评估并优化后的教案文本
        """
        import re
        
        print("\n====================================")
        print("🎯 理论引用质量三维评估开始")
        print("====================================")
        
        # 定义所有需要理论依据的教学环节
        required_sections = [
            "知识与技能目标",
            "过程与方法目标",
            "情感态度与价值观目标",
            "核心素养目标",
            "教学重点",
            "教学难点",
            "教学方法",
            "教学手段",
            "创设情境",
            "提出问题",
            "激发兴趣",
            "自主探究",
            "小组合作",
            "教师引导",
            "典型例题",
            "解题思路",
            "易错点辨析",
            "基础训练",
            "综合应用",
            "分层作业",
            "知识梳理",
            "方法提炼",
            "反思评价",
            "基础作业",
            "拓展作业",
            "板书设计",
            "预期效果",
            "可能的问题",
            "改进方向"
        ]
        
        # 1. 完整性评估
        print("\n📊 完整性评估")
        # 检查每个环节是否都有理论依据
        missing_sections = []
        for section in required_sections:
            if re.search(rf"###.*?{re.escape(section)}.*?📌 理论依据", lesson_plan, re.DOTALL) is None:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ 发现 {len(missing_sections)} 个环节缺少理论依据: {', '.join(missing_sections)}")
            # 为缺失的环节添加理论依据
            for section in missing_sections:
                # 根据教学方法和内容类型调整理论推荐
                recommended_theories = self._get_recommended_theories(section, teaching_method, content_type)
                
                # 选择一个合适的理论
                selected_theory = None
                for theory_key in recommended_theories:
                    if theory_key in self.theory_cards_index:
                        selected_theory = theory_key
                        break
                
                if selected_theory:
                    theory_info = self.theory_cards_index[selected_theory]
                    theory_name = theory_info["name"]
                    core_view = theory_info["core_view"]
                    teaching_inspiration = theory_info.get("teaching_inspiration", "")
                    teaching_inspiration_elements = theory_info.get("teaching_inspiration_elements", [])
                    
                    # 生成理论依据（使用简洁的 Markdown 格式）
                    if teaching_inspiration_elements:
                        inspiration_elements_str = "、".join(teaching_inspiration_elements[:3])  # 限制最多3个要点
                        theory_reference = f"""

**📌 理论依据**

**【{selected_theory}：{theory_name}】**

- **核心观点**：{core_view[:100]}...
- **教学启发**：{teaching_inspiration[:80]}...
- **应用场景**：设计体现了教学启发中的：{inspiration_elements_str}"""
                    else:
                        theory_reference = f"""

**📌 理论依据**

**【{selected_theory}：{theory_name}】**

- **核心观点**：{core_view[:150]}...
- **应用场景**：指导{section}环节的教学设计，具体体现了{theory_name}的核心观点"""
                    
                    # 找到环节位置并插入理论依据
                    section_pattern = rf"(###.*?{re.escape(section)}.*?)(###|$)"
                    match = re.search(section_pattern, lesson_plan, re.DOTALL)
                    if match:
                        insert_position = match.end(1)
                        lesson_plan = lesson_plan[:insert_position] + f"\n\n{theory_reference}" + lesson_plan[insert_position:]
                        print(f"✅ 为 {section} 环节添加理论依据: {selected_theory}：{theory_name}")
        else:
            print("✅ 所有环节都有理论依据")
        
        # 2. 准确性评估
        print("\n📊 准确性评估")
        # 提取所有理论引用
        pattern = r"📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
        references = re.findall(pattern, lesson_plan)
        
        # 检查无效引用
        invalid_references = []
        for card_key, theory_name in references:
            if card_key not in self.theory_cards_index:
                invalid_references.append((card_key, theory_name))
        
        if invalid_references:
            print(f"⚠️ 发现 {len(invalid_references)} 个无效理论引用")
            # 修正无效引用
            for card_key, theory_name in invalid_references:
                # 尝试找到最接近的有效理论卡片
                valid_card = None
                for key in self.theory_cards_index:
                    if theory_name in self.theory_cards_index[key]["name"]:
                        valid_card = key
                        break
                
                if valid_card:
                    # 替换为有效引用
                    old_ref = f"[{card_key}：{theory_name}]"
                    card_name = self.theory_cards_index[valid_card]["name"]
                    new_ref = f"[{valid_card}：{card_name}]"
                    lesson_plan = lesson_plan.replace(old_ref, new_ref)
                    print(f"✅ 修正无效引用: {old_ref} → {new_ref}")
                else:
                    # 如果找不到匹配的理论，使用推荐的理论
                    recommended_theories = self._get_recommended_theories("教学方法", teaching_method, content_type)
                    if recommended_theories:
                        valid_card = recommended_theories[0]
                        old_ref = f"[{card_key}：{theory_name}]"
                        card_name = self.theory_cards_index[valid_card]["name"]
                        new_ref = f"[{valid_card}：{card_name}]"
                        lesson_plan = lesson_plan.replace(old_ref, new_ref)
                        print(f"⚠️ 替换无效引用为推荐理论: {old_ref} → {new_ref}")
        else:
            print("✅ 所有理论引用均有效")
        
        # 3. 深度评估
        print("\n📊 深度评估")
        # 检查理论引用深度
        shallow_references = []
        
        # 提取所有理论引用位置
        ref_pattern = r"###.*?(📌 理论依据：\[(理论卡片\d+)：([^\]]+)\].*?)(###|$)"
        ref_matches = re.findall(ref_pattern, lesson_plan, re.DOTALL)
        
        for match in ref_matches:
            ref_content = match[0]
            card_key = match[1]
            theory_name = match[2]
            
            # 检查是否为表层引用（仅提及理论名称，应用场景描述笼统）
            if len(ref_content) < 150 or "具体体现" not in ref_content:
                shallow_references.append((card_key, theory_name))
        
        if shallow_references:
            print(f"⚠️ 发现 {len(shallow_references)} 个表层引用，需要深度优化")
            # 优化深度不足的引用
            for card_key, theory_name in shallow_references:
                if card_key in self.theory_cards_index:
                    theory_info = self.theory_cards_index[card_key]
                    core_view = theory_info["core_view"]
                    teaching_inspiration = theory_info.get("teaching_inspiration", "")
                    
                    # 生成深度结合的理论依据（使用新的分点格式）
                    deep_content = f"""**📌 理论依据**
- **理论卡片**：{card_key} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：通过设计具体的教学活动，如...，充分体现了{theory_name}的核心观点，实现了理论与实践的深度融合"""
                    
                    # 替换表层引用
                    old_pattern = rf"📌 理论依据：\[{card_key}：{re.escape(theory_name)}\].*? - 应用场景：.*?\*\*"
                    lesson_plan = re.sub(old_pattern, deep_content, lesson_plan, flags=re.DOTALL)
                    print(f"✅ 优化理论引用深度: {card_key}：{theory_name}")
        else:
            print("✅ 所有理论引用均为深度结合")
        
        print("\n====================================")
        print("🎯 理论引用质量三维评估完成")
        print("====================================")
        
        return lesson_plan
