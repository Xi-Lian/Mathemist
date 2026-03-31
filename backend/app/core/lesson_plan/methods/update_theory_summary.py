from .._shared import *


class _UpdateTheorySummaryMixin:
    def _update_theory_summary(self, lesson_plan: str, references: List[tuple]) -> str:
        """
        更新教案中的理论依据使用总结
        
        Args:
            lesson_plan: 教案文本
            references: 有效理论引用列表
        
        Returns:
            更新后的教案文本
        """
        # 提取教案中的各个环节
        sections = [
            "教学目标设计", "教学重难点分析", "教学方法与策略",
            "情境导入", "新知探究", "典例分析", "跟踪训练", "课堂小结", "作业布置",
            "板书设计", "教学反思"
        ]
        
        # 构建理论使用统计
        theory_usage = {}
        for card_key, theory_name in references:
            if card_key not in theory_usage:
                theory_usage[card_key] = {
                    "name": theory_name,
                    "sections": [],
                    "core_view": self.theory_cards_index.get(card_key, {}).get("core_view", "")
                }
        
        # 简单地为每个理论分配一些环节（实际应用中可能需要更复杂的分析）
        for i, (card_key, _) in enumerate(references):
            if card_key in theory_usage:
                section = sections[i % len(sections)]
                if section not in theory_usage[card_key]["sections"]:
                    theory_usage[card_key]["sections"].append(section)
        
        # 生成新的理论依据使用总结
        summary_table = "| 理论依据 | 应用环节 | 理论核心观点 | 具体作用 |\n"
        summary_table += "|---------|---------|-------------|---------|\n"
        
        for card_key, info in theory_usage.items():
            sections_str = ", ".join(info["sections"])
            core_view = info["core_view"]
            # 简单生成具体作用描述
            role = f"指导{sections_str}环节的教学设计，体现了{info['name']}的应用价值"
            
            summary_table += f"| [{card_key}：{info['name']}] | {sections_str} | {core_view} | {role} |\n"
        
        # 替换原有的理论依据使用总结
        import re
        pattern = r"### 📚 本教案使用的理论依据汇总\n\n.*?### 🎯 理论依据使用亮点"
        replacement = f"### 📚 本教案使用的理论依据汇总\n\n{summary_table}\n### 🎯 理论依据使用亮点"
        
        updated_lesson_plan = re.sub(pattern, replacement, lesson_plan, flags=re.DOTALL)
        
        print("✅ 理论依据使用总结已更新")
        return updated_lesson_plan
