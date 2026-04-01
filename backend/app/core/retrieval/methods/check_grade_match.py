from .._shared import *
from ..grade_policy import strict_grade_match


class _CheckGradeMatchMixin:
    def _check_grade_match(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V28.0：应用年级筛选
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
        
        Returns:
            筛选结果字典，包含pass和reason
        """
        source_file = metadata.get('source_file', '')
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        if not resource_grade:
            return {'pass': True, 'reason': '无法推断资源年级'}
        passed, reason = strict_grade_match(resource_grade, grade_info)
        if passed:
            return {'pass': True, 'reason': reason}
        return {'pass': False, 'reason': f'年级不匹配: 资源是{resource_grade.get("grade")}，查询要求{grade_info.get("grade")}'}
