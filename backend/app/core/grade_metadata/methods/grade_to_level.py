from .._shared import *


class _GradeToLevelMixin:
    def _grade_to_level(self, grade: str) -> int:
        """
        将年级字符串转换为数字级别
        
        Args:
            grade: 年级字符串（如"高一上学期"）
            
        Returns:
            数字级别（便于比较）
        """
        grade_map = {
            '高一上学期': 10,
            '高一下学期': 11,
            '高二上学期': 12,
            '高二下学期': 13,
            '高三': 14,
            '高一': 10,
            '高二': 12,
            '高三': 14,
        }
        return grade_map.get(grade, 0)
