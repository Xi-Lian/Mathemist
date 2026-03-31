from .._shared import *


class _AnalyzeContentTypeMixin:
    def _analyze_content_type(self, user_input: str) -> str:
        """
        分析用户输入中的教学内容类型
        
        Args:
            user_input: 用户需求
        
        Returns:
            教学内容类型
        """
        import re
        
        # 定义教学内容类型关键词
        content_types = {
            "概念教学": ["概念", "定义", "性质", "定理", "公式推导"],
            "技能训练": ["训练", "练习", "解题", "应用", "计算"],
            "问题解决": ["问题", "解决", "应用", "探究", "案例"],
            "复习总结": ["复习", "总结", "梳理", "回顾", "系统"],
            "项目学习": ["项目", "实践", "综合", "研究", "探究"]
        }
        
        # 检测教学内容类型
        for content_type, keywords in content_types.items():
            for keyword in keywords:
                if re.search(keyword, user_input, re.IGNORECASE):
                    return content_type
        
        # 根据课题名称推断内容类型
        # 常见概念教学课题
        concept_topics = ["函数", "指数函数", "对数函数", "三角函数", "立体几何", "解析几何", "概率", "统计"]
        for topic in concept_topics:
            if topic in user_input:
                return "概念教学"
        
        # 默认内容类型
        return "概念教学"
