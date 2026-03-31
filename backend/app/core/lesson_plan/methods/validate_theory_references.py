from .._shared import *


class _ValidateTheoryReferencesMixin:
    def _validate_theory_references(self, lesson_plan: str, teaching_method: str = "讲授式", content_type: str = "概念教学") -> str:
        """
        验证教案中的理论引用
        
        Args:
            lesson_plan: 生成的教案文本
            teaching_method: 教学方法类型
            content_type: 教学内容类型
        
        Returns:
            验证并修正后的教案文本
        """
        import re
        
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
        
        # 提取所有理论引用
        pattern = r"📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
        references = re.findall(pattern, lesson_plan)
        
        print(f"🔍 检测到 {len(references)} 个理论引用")
        
        # 检查引用的有效性和多样性
        valid_references = []
        invalid_references = []
        used_theories = set()
        
        for card_key, theory_name in references:
            if card_key in self.theory_cards_index:
                valid_references.append((card_key, theory_name))
                used_theories.add(card_key)
            else:
                invalid_references.append((card_key, theory_name))
        
        # 检查理论多样性
        if len(used_theories) < 3:
            print(f"⚠️ 理论引用多样性不足，仅使用了 {len(used_theories)} 个不同理论")
        else:
            print(f"✅ 理论引用多样性良好，使用了 {len(used_theories)} 个不同理论")
        
        # 检查无效引用
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
                    # 如果找不到匹配的理论，使用第一个理论卡片作为替代
                    first_card = list(self.theory_cards_index.keys())[0]
                    old_ref = f"[{card_key}：{theory_name}]"
                    first_card_name = self.theory_cards_index[first_card]["name"]
                    new_ref = f"[{first_card}：{first_card_name}]"
                    lesson_plan = lesson_plan.replace(old_ref, new_ref)
                    print(f"⚠️ 替换无效引用为默认理论: {old_ref} → {new_ref}")
        else:
            print("✅ 所有理论引用均有效")
        
        # 检查每个环节是否都有理论引用
        missing_sections = []
        for section in required_sections:
            if re.search(rf"###.*?{re.escape(section)}.*?📌 理论依据", lesson_plan, re.DOTALL) is None:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"⚠️ 发现 {len(missing_sections)} 个环节缺少理论依据: {', '.join(missing_sections)}")
            # 为缺失的环节添加理论依据
            for section in missing_sections:
                # 根据教学方法和内容类型调整理论推荐
                recommended_theories = self._get_dynamic_recommended_theories(section, teaching_method, content_type)
                
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
                    
                    # 生成理论依据（使用简洁的分点格式，无边框）
                    if teaching_inspiration_elements:
                        inspiration_elements_str = "、".join(teaching_inspiration_elements[:3])  # 限制最多3个要点
                        
                        # 处理应用场景
                        application_text = f"设计体现了教学启发中的：{inspiration_elements_str}"
                        
                        theory_reference = f"""**📌 理论依据**
- **理论卡片**：{selected_theory} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：{application_text}"""
                    else:
                        # 处理应用场景
                        application_text = f"指导{section}环节的教学设计，体现了{theory_name}的应用价值"
                        
                        theory_reference = f"""**📌 理论依据**
- **理论卡片**：{selected_theory} - {theory_name}
- **核心观点**：{core_view}
- **应用场景**：{application_text}"""
                    
                    # 清理多余的空行
                    theory_reference = theory_reference.replace('\n\n', '\n')
                    
                    # 找到环节位置并插入理论依据
                    section_pattern = rf"(###.*?{re.escape(section)}.*?)(###|$)"
                    match = re.search(section_pattern, lesson_plan, re.DOTALL)
                    if match:
                        insert_position = match.end(1)
                        # 检查该位置是否已经有理论依据，避免重复添加
                        if "📌 理论依据" not in lesson_plan[match.start(1):insert_position]:
                            lesson_plan = lesson_plan[:insert_position] + f"\n\n{theory_reference}" + lesson_plan[insert_position:]
                            print(f"✅ 为 {section} 环节添加理论依据: {selected_theory}：{theory_name}")
        else:
            print("✅ 所有环节都有理论依据")
        
        # 检查理论选择是否与教学方法匹配
        lesson_plan = self._validate_theory_method_match(lesson_plan, teaching_method)
        
        # 检查理论引用的一致性
        import re
        required_sections = [
            "知识与技能目标", "过程与方法目标", "情感态度与价值观目标",
            "核心素养目标", "教学重点", "教学难点", "教学方法", "教学手段",
            "创设情境", "提出问题", "激发兴趣", "自主探究", "小组合作",
            "教师引导", "典型例题", "解题思路", "易错点辨析", "基础训练",
            "综合应用", "分层作业", "知识梳理", "方法提炼", "反思评价",
            "基础作业", "拓展作业", "板书设计", "预期效果", "可能的问题", "改进方向"
        ]
        
        # 构建环节-理论映射
        section_theory_map = {}
        for section in required_sections:
            section_pattern = rf"###.*?{re.escape(section)}.*?📌 理论依据：\[(理论卡片\d+)：([^\]]+)\]"
            match = re.search(section_pattern, lesson_plan, re.DOTALL)
            if match:
                section_theory_map[section] = match.group(1)
        
        # 检查一致性
        inconsistent_sections = []
        for section, theory_key in section_theory_map.items():
            recommended_theories = self._get_recommended_theories(section, teaching_method, content_type)
            if recommended_theories and theory_key not in recommended_theories:
                inconsistent_sections.append((section, theory_key, recommended_theories[0]))
        
        # 修正不一致的理论引用
        if inconsistent_sections:
            print(f"⚠️ 发现 {len(inconsistent_sections)} 个理论引用不一致的环节")
            for section, old_theory_key, new_theory_key in inconsistent_sections:
                old_theory_name = self.theory_cards_index.get(old_theory_key, {}).get("name", "未知理论")
                new_theory_name = self.theory_cards_index.get(new_theory_key, {}).get("name", "未知理论")
                
                old_ref_pattern = rf"(###.*?{re.escape(section)}.*?)📌 理论依据：\[{old_theory_key}：{re.escape(old_theory_name)}\]"
                new_ref = f"📌 理论依据：[{new_theory_key}：{new_theory_name}]"
                
                lesson_plan = re.sub(old_ref_pattern, rf"\1{new_ref}", lesson_plan, flags=re.DOTALL)
                print(f"✅ 修正 {section} 环节的理论引用: {old_theory_key}：{old_theory_name} → {new_theory_key}：{new_theory_name}")
        else:
            print("✅ 所有理论引用均一致")
        
        # 更新理论依据使用总结
        lesson_plan = self._update_theory_summary(lesson_plan, valid_references)
        
        return lesson_plan
