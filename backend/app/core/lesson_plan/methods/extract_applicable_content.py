from .._shared import *


class _ExtractApplicableContentMixin:
    def _extract_applicable_content(self, theory_name: str, core_view: str) -> str:
        """
        动态提取理论适用的内容类型（基于理论名称和核心观点的关键词分析）
        
        Args:
            theory_name: 理论名称
            core_view: 理论核心观点
        
        Returns:
            适用的内容类型
        """
        import re
        
        # 从理论名称和核心观点中提取关键词
        combined_text = theory_name + " " + core_view
        
        # 定义内容类型关键词
        content_keywords = {
            "概念教学": ["概念", "定义", "原理", "性质", "规律", "公式", "定理"],
            "技能训练": ["技能", "技巧", "方法", "操作", "计算", "解题", "练习"],
            "问题解决": ["问题", "解决", "应用", "实际", "情境", "任务", "挑战"],
            "知识讲解": ["知识", "讲解", "传递", "信息", "内容", "材料"],
            "实验教学": ["实验", "实践", "操作", "观察", "验证", "探究"],
            "项目学习": ["项目", "综合", "实践", "应用", "研究", "创作"],
            "学习策略": ["策略", "方法", "技巧", "元认知", "监控", "反思"],
            "记忆策略": ["记忆", "保持", "提取", "存储", "编码"],
            "复习总结": ["复习", "总结", "梳理", "归纳", "整合", "网络"],
            "学习评价": ["评价", "反馈", "评估", "测试", "考核"],
            "习惯养成": ["习惯", "行为", "规范", "养成", "塑造"],
            "个性化学习": ["个体", "差异", "因材施教", "多元", "智能"]
        }
        
        # 匹配内容类型
        matched_content = []
        for content, keywords in content_keywords.items():
            for keyword in keywords:
                if keyword in combined_text:
                    matched_content.append(content)
                    break
        
        # 如果没有匹配到，返回"所有内容类型"
        if not matched_content:
            return "所有内容类型"
        
        # 去重
        matched_content = list(set(matched_content))
        
        # 如果匹配到多个内容类型，返回前4个
        if len(matched_content) > 4:
            matched_content = matched_content[:4]
        
        return "、".join(matched_content)
