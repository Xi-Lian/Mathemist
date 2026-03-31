from .._shared import *


class _BuildLessonPlanResponseMixin:
    def _build_lesson_plan_response(self, state: Any) -> str:
        """
        构建教案生成响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            教案响应文本
        """
        response_parts = []
        
        # 优先检查是否有引导响应（当信息不完整时）
        response = self._get_state_value(state, "response", "")
        if response:
            # 如果有引导响应，直接返回引导信息
            return response
        
        # 添加教案
        lesson_plan = self._get_state_value(state, "lesson_plan", "")
        if lesson_plan:
            response_parts.append("="*50)
            response_parts.append("📚 **生成的教案**")
            response_parts.append("="*50)
            response_parts.append(lesson_plan)
            response_parts.append("\n")
        
        # 添加检索到的资源
        resources = self._format_resources(state, scenario="generation")
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
