from .._shared import *


class _AnalyzeStudentLevelMixin:
    def _analyze_student_level(self, user_input: str) -> str:
        """
        分析用户输入中的学生水平
        
        Args:
            user_input: 用户需求
        
        Returns:
            学生水平
        """
        # 定义学生水平关键词
        student_levels = {
            "小学": ["小学", "低年级", "中年级", "高年级", "小学生"],
            "初中": ["初中", "初一", "初二", "初三", "初中生"],
            "高中": ["高中", "高一", "高二", "高三", "高中生"],
            "大学": ["大学", "本科生", "研究生", "大学生"]
        }
        
        # 匹配学生水平
        for level, keywords in student_levels.items():
            for keyword in keywords:
                if keyword in user_input:
                    return level
        
        return "初中"  # 默认值
