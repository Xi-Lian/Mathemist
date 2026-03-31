from .._shared import *


class _GetGradeStatisticsMixin:
    def get_grade_statistics(self, resources: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        统计资源列表中的年级分布
        
        Args:
            resources: 资源列表
            
        Returns:
            年级分布统计
        """
        stats = {}
        for resource in resources:
            grade = resource.get('grade', '未知')
            stats[grade] = stats.get(grade, 0) + 1
        return stats


# 全局单例实例
_grade_enricher = None
