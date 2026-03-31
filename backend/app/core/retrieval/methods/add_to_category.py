from .._shared import *


class _AddToCategoryMixin:
    def _add_to_category(
        self, 
        classified: Dict[str, List], 
        resource_type: str, 
        resource: Dict[str, Any]
    ):
        """
        将资源添加到对应分类
        
        Args:
            classified: 分类字典
            resource_type: 资源类型
            resource: 资源对象
        """
        category_map = {
            "lesson_plan": "lesson_plan_patterns",
            "visualization": "visualization_examples",
            "exercise": "exercise_resources",
            "courseware": "courseware_resources",
            "lesson_case": "lesson_case_resources",
            "ggb": "ggb_resources",
            "syllabus": "syllabus_resources",
            "theory": "theory_resources"
        }
        
        category = category_map.get(resource_type, "theory_resources")
        # 在资源对象上设置_category属性，供_reclassify_by_relevance方法使用
        resource["_category"] = category
        classified[category].append(resource)
