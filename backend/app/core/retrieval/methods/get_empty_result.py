from .._shared import *


class _GetEmptyResultMixin:
    def _get_empty_result(self) -> Dict[str, Any]:
        """
        获取空的检索结果
        
        Returns:
            空结果字典
        """
        return {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "exercise_resources": [],
            "visualization_examples": [],
            "general_resources": [],
            "courseware_resources": [],
            "lesson_case_resources": [],
            "ggb_resources": [],
            "syllabus_resources": [],
            "_hidden_resources": [],
            "_hidden_count": 0,
            "_total_count": 0
        }
