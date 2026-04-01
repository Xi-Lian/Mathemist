from .._shared import *
from ..grade_policy import flexible_grade_score


class _ApplyFlexibleGradeFilterMixin:
    def _apply_flexible_grade_filter(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V32.0：应用灵活的年级筛选（用于宽泛查询）
        
        策略：
        - 宽泛查询时，放宽年级筛选，允许各年级相关内容
        - 优先返回查询年级的内容，但也允许其他年级的相关内容
        - 通过调整相关性得分来体现优先级
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
            
        Returns:
            筛选结果字典
        """
        source_file = metadata.get('source_file', '')
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        if not resource_grade:
            return {'pass': True, 'reason': '无法推断资源年级', 'score_adjustment': 0.8}
        return flexible_grade_score(resource_grade, grade_info)
