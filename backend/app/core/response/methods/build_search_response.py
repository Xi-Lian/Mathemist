from .._shared import *


class _BuildSearchResponseMixin:
    def _build_search_response(self, state: Any) -> str:
        """
        构建资源搜索响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            搜索响应文本
        """
        retrieved_resources = self._get_state_value(state, "retrieved_resources", {}) or {}
        user_input = self._get_state_value(state, "user_input", "")
        scope_notice = self._get_state_value(state, "scope_notice", None)

        resource_groups = [
            ("教案资源", retrieved_resources.get("lesson_plan_patterns", [])),
            ("习题资源", retrieved_resources.get("exercise_resources", [])),
            ("课件资源", retrieved_resources.get("courseware_resources", [])),
            ("课例资源", retrieved_resources.get("lesson_case_resources", [])),
            ("GGB资源", retrieved_resources.get("ggb_resources", [])),
            ("教学大纲", retrieved_resources.get("syllabus_resources", [])),
            ("可视化示例", retrieved_resources.get("visualization_examples", [])),
        ]

        category_count = sum(1 for _, items in resource_groups if items)
        total_count = sum(len(items) for _, items in resource_groups)
        formatted_resources = self._format_resources(state, scenario="search")

        if formatted_resources == "未找到相关资源":
            return formatted_resources

        intro_parts = []
        if user_input:
            intro_parts.append(f"你要找的是“{user_input}”相关资源。")
        if category_count > 0:
            intro_parts.append(
                f"我先按推荐顺序整理了 {category_count} 类资源，共 {total_count} 条候选。"
            )
        intro_parts.append("越靠前越值得先看；每条保留适配说明、内容预览和文件路径。")

        if isinstance(scope_notice, dict) and scope_notice.get("message"):
            intro_parts.append(scope_notice["message"])

        return "\n".join([
            "".join(intro_parts),
            "",
            formatted_resources,
        ])
