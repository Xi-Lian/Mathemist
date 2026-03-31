from .._shared import *


class _BuildVisualizationResponseMixin:
    def _build_visualization_response(self, state: Any) -> str:
        """
        构建可视化建议响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            可视化响应文本
        """
        response_parts = []
        
        # 添加GGB设计建议（优先）
        ggb_suggestions = self._get_state_value(state, "ggb_design_suggestions", None)
        if ggb_suggestions:
            response_parts.append("="*50)
            response_parts.append("🎨 **GeoGebra动态图设计建议**")
            response_parts.append("="*50)
            for i, suggestion in enumerate(ggb_suggestions, 1):
                if suggestion.get("error"):
                    response_parts.append(f"❌ 第{i}个GGB资源设计建议生成失败: {suggestion.get('error')}\n")
                else:
                    response_parts.append(f"\n### {i}. {suggestion.get('metadata', {}).get('ggb_filename', '未知')}")
                    response_parts.append(suggestion.get("design_steps", ""))
                    response_parts.append("\n---")
        
        # 添加可视化建议
        suggestions = self._get_state_value(state, "visualization_suggestions", "")
        if suggestions:
            response_parts.append("\n" + "="*50)
            response_parts.append("🎨 **可视化设计建议**")
            response_parts.append("="*50)
            response_parts.append(suggestions)
            response_parts.append("\n")
        
        # 添加检索到的资源
        resources = self._format_resources(state, scenario="search")
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
