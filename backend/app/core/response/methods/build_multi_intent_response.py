from .._shared import *


class _BuildMultiIntentResponseMixin:
    def _build_multi_intent_response(self, state: Any, processed_intents: list) -> str:
        """
        构建多意图响应
        
        Args:
            state: 状态对象
            processed_intents: 已处理的意图列表
        
        Returns:
            整合后的响应文本
        """
        response_parts = []
        
        # 添加多意图处理说明
        response_parts.append("🎯 **智能助手为您提供多维度服务**\n")
        
        # 按优先级添加各意图的响应内容
        # 1. 教案生成内容
        if "generate_lesson_plan" in processed_intents:
            lesson_plan = self._get_state_value(state, "lesson_plan", "")
            if lesson_plan:
                response_parts.append("\n" + "="*50)
                response_parts.append("📚 **生成的教案**")
                response_parts.append("="*50)
                response_parts.append(lesson_plan)
        
        # 2. 可视化建议内容
        if "visualization" in processed_intents:
            suggestions = self._get_state_value(state, "visualization_suggestions", "")
            if suggestions:
                response_parts.append("\n" + "="*50)
                response_parts.append("🎨 **可视化设计建议**")
                response_parts.append("="*50)
                response_parts.append(suggestions)
        
        # 3. GGB设计建议内容
        if "ggb_design" in processed_intents:
            ggb_suggestions = self._get_state_value(state, "ggb_design_suggestions", None)
            if ggb_suggestions:
                response_parts.append("\n" + "="*50)
                response_parts.append("🔧 **GeoGebra动态图设计建议**")
                response_parts.append("="*50)
                for i, suggestion in enumerate(ggb_suggestions, 1):
                    if suggestion.get("error"):
                        response_parts.append(f"❌ 第{i}个GGB资源设计建议生成失败: {suggestion.get('error')}")
                    else:
                        response_parts.append(f"\n### {i}. {suggestion.get('metadata', {}).get('ggb_filename', '未知')}")
                        response_parts.append(suggestion.get("design_steps", ""))
        
        # 4. 添加检索到的资源
        # 根据是否包含教案生成意图来决定场景
        resource_scenario = "generation" if "generate_lesson_plan" in processed_intents else "search"
        resources = self._format_resources(state, scenario=resource_scenario)
        if resources:
            response_parts.append("\n" + "="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
