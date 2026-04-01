from .._shared import *
from ..grade_policy import strict_grade_match


class _ApplyGradeFilterMixin:
    def _apply_grade_filter(self, classified: Dict[str, Any], grade_info: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """
        V33.0: 应用年级过滤
        
        Args:
            classified: 分类后的资源
            grade_info: 年级信息
            query: 查询文本
        
        Returns:
            过滤后的资源
        """
        target_grade = grade_info.get('grade', '')
        if not target_grade:
            return classified

        print(f"   🎓 应用统一年级过滤: 目标年级='{target_grade}'")
        for category in classified:
            if isinstance(classified[category], list):
                filtered = []
                for resource in classified[category]:
                    source_file = resource.get('source', '') or resource.get('source_file', '')
                    title = resource.get('title', '')
                    metadata = resource.get('metadata', {})
                    inferred = self.grade_enricher.infer_grade_from_path(source_file)
                    if not inferred:
                        filtered.append(resource)
                    else:
                        passed, reason = strict_grade_match(inferred, grade_info)
                        if passed:
                            filtered.append(resource)
                            print(f"   🎓 年级保留: '{title}' ({reason})")
                        else:
                            print(f"   🎓 年级过滤移除: '{title}' (目标年级: {target_grade})")
                    if not inferred:
                        print(f"   🎓 年级未知保留: '{title}'")
                classified[category] = filtered
                print(f"   📊 {category} 过滤后剩余 {len(filtered)} 条资源")

        return classified
