from .._shared import *


class _AnalyzeClassTypeMixin:
    def _analyze_class_type(self, user_input: str) -> str:
        """
        分析用户输入中的课型
        
        Args:
            user_input: 用户需求
        
        Returns:
            课型
        """
        # 定义课型关键词
        class_types = {
            "新授课": ["新授", "新课", "新内容", "新知识点"],
            "复习课": ["复习", "回顾", "总结", "梳理"],
            "练习课": ["练习", "训练", "巩固", "应用"],
            "实验课": ["实验", "实践", "操作", "探究"],
            "讲评课": ["讲评", "点评", "分析", "讲解"]
        }
        
        # 匹配课型
        for class_type, keywords in class_types.items():
            for keyword in keywords:
                if keyword in user_input:
                    return class_type
        
        return "新授课"  # 默认值
