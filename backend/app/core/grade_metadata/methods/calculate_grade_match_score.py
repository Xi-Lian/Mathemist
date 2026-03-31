from .._shared import *


class _CalculateGradeMatchScoreMixin:
    def calculate_grade_match_score(
        self, 
        resource_grade_level: int, 
        query_grade: str,
        tolerance: int = 1
    ) -> float:
        """
        计算年级匹配得分
        
        Args:
            resource_grade_level: 资源的年级级别
            query_grade: 查询中的年级要求
            tolerance: 允许的年级差距（默认1个学期）
            
        Returns:
            匹配得分 (0-1)
        """
        # 解析查询中的年级
        query_level = self._parse_query_grade(query_grade)
        
        if query_level == 0:
            # 查询中没有明确的年级要求，返回中性分数
            return 0.5
        
        if resource_grade_level == 0:
            # 资源没有年级信息，返回较低分数
            return 0.3
        
        # 计算年级差距
        diff = abs(resource_grade_level - query_level)
        
        if diff == 0:
            return 1.0
        elif diff <= tolerance:
            return 0.8 - (diff - 1) * 0.2
        elif diff <= tolerance + 1:
            return 0.5
        else:
            return 0.0
