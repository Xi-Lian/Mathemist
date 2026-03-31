from .._shared import *


class _CheckTheoryConsistencyMixin:
    def _check_theory_consistency(self, lesson_plan: str, teaching_method: str, content_type: str) -> str:
        """
        检查理论引用的一致性
        
        Args:
            lesson_plan: 教案内容
            teaching_method: 教学方法
            content_type: 教学内容类型
        
        Returns:
            检查后的教案内容
        """
        import re
        
        # 定义所有需要理论依据的教学环节
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
        
        return lesson_plan
