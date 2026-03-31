from .._shared import *


class _GetSummaryMixin:
    def _get_summary(self, classified: Dict[str, Any]) -> str:
        """
        生成检索结果摘要
        
        Args:
            classified: 分类后的资源
        
        Returns:
            摘要字符串
        """
        summary_parts = []
        
        if classified["theory_resources"]:
            summary_parts.append(f"理论{len(classified['theory_resources'])}条")
        if classified["lesson_plan_patterns"]:
            summary_parts.append(f"教案{len(classified['lesson_plan_patterns'])}条")
        if classified["exercise_resources"]:
            summary_parts.append(f"习题{len(classified['exercise_resources'])}条")
        if classified["visualization_examples"]:
            summary_parts.append(f"可视化{len(classified['visualization_examples'])}条")
        if classified["courseware_resources"]:
            summary_parts.append(f"课件{len(classified['courseware_resources'])}条")
        if classified["lesson_case_resources"]:
            summary_parts.append(f"课例{len(classified['lesson_case_resources'])}条")
        if classified["ggb_resources"]:
            summary_parts.append(f"GGB{len(classified['ggb_resources'])}条")
        if classified["syllabus_resources"]:
            summary_parts.append(f"教学大纲{len(classified['syllabus_resources'])}条")
        
        return ", ".join(summary_parts) if summary_parts else "无结果"
