from .._shared import *


class _AnalyzeTeachingMethodMixin:
    def _analyze_teaching_method(self, user_input: str) -> str:
        """
        分析用户输入中的教学方法
        
        Args:
            user_input: 用户需求
        
        Returns:
            教学方法类型
        """
        import re
        
        # 定义教学方法关键词
        teaching_methods = {
            "探究式": ["探究式", "自主探究", "发现学习", "问题导向", "项目学习", "互动", "互动性", "强互动", "互动教学", "师生互动", "生生互动"],
            "合作学习": ["合作学习", "小组合作", "同伴学习", "协作学习"],
            "翻转课堂": ["翻转课堂", "翻转教学"],
            "混合式": ["混合式", "线上线下", "混合教学"],
            "讲授式": ["讲授式", "讲解式", "传统教学", "教师主导", "课堂讲授"]
        }

        # 检测教学方法
        for method, keywords in teaching_methods.items():
            for keyword in keywords:
                if re.search(keyword, user_input, re.IGNORECASE):
                    return method

        # 默认教学方法
        return "讲授式"
