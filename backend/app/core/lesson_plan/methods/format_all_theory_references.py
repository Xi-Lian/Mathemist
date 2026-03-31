from .._shared import *


class _FormatAllTheoryReferencesMixin:
    def _format_all_theory_references(self, lesson_plan: str) -> str:
        """
        转换所有理论依据为新的简洁格式，并处理标题格式
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            格式化后的教案内容
        """
        import re
        
        # 1. 处理标题格式，添加正确的一级标题标记（避免重复添加）
        # 只对没有井号的标题添加井号
        lesson_plan = re.sub(r'^\s*(?!#)(《.+》教学设计)', r'# \1', lesson_plan, flags=re.MULTILINE)
        # 也处理可能在中间出现的标题格式（避免重复添加）
        lesson_plan = re.sub(r'\n\s*(?!#)(《.+》教学设计)', r'\n# \1', lesson_plan)
        
        # 2. 匹配旧格式的理论依据（使用更精确的正则表达式，避免误匹配）
        # 使用非贪婪匹配，确保只匹配完整的理论依据块
        pattern = r"\*\*📌 理论依据：\[(理论卡片[^\]]+)\] - (.*?) - 应用场景：(.*?)\*\*"
        matches = re.findall(pattern, lesson_plan, re.DOTALL)
        
        # 保存所有需要替换的内容，避免在遍历过程中修改字符串导致的问题
        replacements = []
        
        for match in matches:
            full_theory_key = match[0]
            core_view = match[1].strip()
            application = match[2].strip()
            
            # 提取理论卡片编号（去掉理论名称）
            theory_key_match = re.match(r"(理论卡片[一二三四五六七八九十百]+)[:：]*(.*)", full_theory_key)
            if theory_key_match:
                theory_key = theory_key_match.group(1)
                theory_name = theory_key_match.group(2)
            else:
                theory_key = full_theory_key
                theory_name = "未知理论"
            
            # 从理论卡片索引中获取完整信息
            if theory_key in self.theory_cards_index:
                theory_info = self.theory_cards_index[theory_key]
                theory_name = theory_info["name"]
                teaching_inspiration = theory_info.get("teaching_inspiration", "")
                teaching_inspiration_elements = theory_info.get("teaching_inspiration_elements", [])
                
                # 清理核心观点和应用场景中的重复内容
                core_view = core_view.replace('**核心观点**', '').strip()
                application = application.replace('**应用场景**', '').strip()
                
                # 生成新的理论依据格式（简洁版，无边框）
                if teaching_inspiration_elements:
                    # 确保教学启发内容不重复
                    teaching_inspiration = teaching_inspiration.replace('**教学启发**', '').strip()
                    new_theory_reference = f"""**📌 理论依据**
- **理论卡片**：{theory_key} - {theory_name}
- **核心观点**：{core_view}
- **教学启发**：{teaching_inspiration}
- **应用场景**：{application}"""
                else:
                    new_theory_reference = f"""**📌 理论依据**
- **理论卡片**：{theory_key} - {theory_name}
- **核心观点**：{core_view}
- **应用场景**：{application}"""
                
                # 准备替换内容
                old_pattern = f"**📌 理论依据：[{full_theory_key}] - {core_view} - 应用场景：{application}**"
                replacements.append((old_pattern, new_theory_reference))
            else:
                pass
        
        # 执行替换，避免在遍历过程中修改字符串
        for old_pattern, new_theory_reference in replacements:
            # 使用re.escape确保特殊字符被正确处理
            safe_old_pattern = re.escape(old_pattern)
            lesson_plan = re.sub(safe_old_pattern, new_theory_reference, lesson_plan, flags=re.DOTALL)
        
        return lesson_plan
