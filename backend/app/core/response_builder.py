"""
响应生成模块

职责：
- 根据意图和生成的结果构建最终响应
- 整合教案、可视化建议和检索到的资源
- 提供结构化的响应输出

依赖：
- model_config (模型配置)
- smart_content_processor (内容处理)
"""

from typing import Dict, Any, List
from .model_config import model_config
from ..smart_content_processor import SmartContentProcessor
from ..config.resource_type_config import (
    get_response_field,
    get_icon,
    get_standard_name,
    get_resource_type_mapping
)


class ResponseBuilder:
    """响应构建器"""
    
    def __init__(self):
        """初始化响应构建器"""
        self.model_config = model_config
        self.content_processor = None
    
    def build(self, state: Any) -> str:
        """
        构建最终响应
        
        Args:
            state: 状态对象，包含意图、教案、建议等（可以是 MathAgentState 对象或字典）
        
        Returns:
            格式化的响应文本
        """
        print(f"\n====================================")
        print(f"📤 响应生成开始")
        
        try:
            # 优先检查是否已经有响应
            response = self._get_state_value(state, "response", "")
            if response:
                print(f"🔀 发现已有响应，直接返回")
                print(f"✅ 响应生成成功，长度: {len(response)}字符")
                return response
            
            # 检查是否有多个处理过的意图
            processed_intents = self._get_state_value(state, "processed_intents", [])
            
            if processed_intents and len(processed_intents) > 1:
                print(f"🎯 检测到多意图处理结果: {processed_intents}")
                response = self._build_multi_intent_response(state, processed_intents)
            else:
                # 单个意图处理
                if hasattr(state, 'intent'):
                    intent = state.intent
                else:
                    intent = state.get("intent", "search")
                print(f"🎯 单个意图: {intent}")
                
                if intent == "generate_lesson_plan":
                    response = self._build_lesson_plan_response(state)
                elif intent == "visualization":
                    response = self._build_visualization_response(state)
                else:
                    response = self._build_search_response(state)
            
            print(f"✅ 响应生成成功，长度: {len(response)}字符")
            
            return response
            
        except Exception as e:
            print(f"❌ 响应生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
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
        resources = self._format_resources(state)
        if resources:
            response_parts.append("\n" + "="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
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
        resources = self._format_resources(state)
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
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
        resources = self._format_resources(state)
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
    def _build_search_response(self, state: Any) -> str:
        """
        构建资源搜索响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            搜索响应文本
        """
        # 对于搜索意图，只显示检索到的资源，不显示生成的内容
        # 确保主次分明，避免生成内容干扰用户对检索结果的判断
        return self._format_resources(state)
    
    def _format_resources(self, state: Any) -> str:
        """
        格式化检索到的资源
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            格式化的资源文本
        """
        # 获取内容处理器
        if self.content_processor is None:
            self.content_processor = self.model_config.get_content_processor()
        
        # 获取检索到的资源
        retrieved_resources = self._get_state_value(state, "retrieved_resources", {})
        
        # 检查是否为 None
        if retrieved_resources is None:
            retrieved_resources = {}
        
        # 获取用户需求
        user_needs = self._get_state_value(state, "user_needs", "")
        resource_types = self._get_state_value(state, "resource_types", [])
        
        print(f"📋 用户需求: {user_needs}")
        print(f"📋 资源类型: {resource_types}")
        
        response_parts = []
        
        # 检查用户是否指定了"资料"或"资源"（表示要所有资源）
        is_all_resources = any(rt in ["资料", "资源"] for rt in resource_types)
        
        # 如果用户明确指定了资源类型，只输出指定的类型
        if resource_types and not is_all_resources:
            print(f"🎯 用户明确指定了资源类型，只输出指定类型")
            print(f"   用户指定类型: {resource_types}")
            
            # 输出用户指定的资源类型
            for user_type in resource_types:
                # 使用统一的资源类型映射
                mapping = get_resource_type_mapping(user_type)
                if mapping:
                    standard_name, db_type, category_key, icon = mapping
                    resources = retrieved_resources.get(category_key, [])
                    if resources:
                        response_parts.append(self._format_resource_category(
                            f"{standard_name}资源", 
                            resources,
                            icon
                        ))
                        print(f"   ✓ 处理类型: {user_type} -> {standard_name} ({len(resources)}条)")
                    else:
                        print(f"   ⚠️ 类型: {user_type} -> {standard_name}，无资源")
                else:
                    print(f"   ⚠️ 未知类型: {user_type}，跳过")
            
            # 如果没有找到任何资源
            if not response_parts:
                response_parts.append(f"未找到{', '.join(resource_types)}相关的资源")
        
        else:
            # 用户没有明确指定资源类型，或者指定了"资料"/"资源"，输出所有找到的资源
            if is_all_resources:
                print(f"🎯 用户指定了'资料'或'资源'，输出所有找到的资源")
            else:
                print(f"🔍 用户未指定资源类型，输出所有找到的资源")
            
            # 格式化教案资源
            lesson_plans = retrieved_resources.get("lesson_plan_patterns", [])
            if lesson_plans:
                response_parts.append(self._format_resource_category(
                    "教案资源", 
                    lesson_plans,
                    "📚"
                ))
            
            # 格式化习题资源
            exercises = retrieved_resources.get("exercise_resources", [])
            if exercises:
                response_parts.append(self._format_resource_category(
                    "习题资源",
                    exercises,
                    "📝"
                ))
            
            # 格式化课件资源
            coursewares = retrieved_resources.get("courseware_resources", [])
            if coursewares:
                response_parts.append(self._format_resource_category(
                    "课件资源",
                    coursewares,
                    "📊"
                ))
            
            # 格式化课例资源
            lesson_cases = retrieved_resources.get("lesson_case_resources", [])
            if lesson_cases:
                response_parts.append(self._format_resource_category(
                    "课例资源",
                    lesson_cases,
                    "🎬"
                ))
            
            # 格式化GGB资源
            ggbs = retrieved_resources.get("ggb_resources", [])
            if ggbs:
                response_parts.append(self._format_resource_category(
                    "GGB资源",
                    ggbs,
                    "🔧"
                ))
            
            # 格式化教学大纲
            syllabi = retrieved_resources.get("syllabus_resources", [])
            if syllabi:
                response_parts.append(self._format_resource_category(
                    "教学大纲",
                    syllabi,
                    "📋"
                ))
            
            # 格式化可视化示例
            visualizations = retrieved_resources.get("visualization_examples", [])
            if visualizations:
                response_parts.append(self._format_resource_category(
                    "可视化示例",
                    visualizations,
                    "🎨"
                ))
            
            # 注意：理论资源不推送给用户，仅用于教案生成
            # 理论资源在教案生成时会被使用，但不会在响应中显示
        
        return "\n".join(response_parts) if response_parts else "未找到相关资源"
    
    def _format_resource_category(
        self, 
        category_name: str, 
        resources: List[Dict[str, Any]],
        icon: str
    ) -> str:
        """
        格式化资源分类
        
        Args:
            category_name: 分类名称
            resources: 资源列表
            icon: 图标
        
        Returns:
            格式化后的文本
        """
        response_parts = [f"\n【{category_name}】\n"]
        
        if not resources:
            return "\n".join(response_parts)
        
        # 过滤掉相似度过低的资源
        filtered_resources = self._filter_by_relevance(resources)
        
        for resource in filtered_resources:
            title = resource.get("title", "未知")
            content = resource.get("content", "")
            relevance = resource.get("relevance", 0)
            source = resource.get("source", "")
            
            # 处理内容
            processed_content = self._process_resource_content(
                category_name, 
                title, 
                content
            )
            
            response_parts.append(f"{icon} {title}")
            response_parts.append(f"   内容: {processed_content}")
            response_parts.append(f"   相似度: {relevance*100:.1f}%")
            response_parts.append(f"   文件路径: {source}")
            response_parts.append("")
        
        # 如果过滤掉了资源，添加提示
        if len(filtered_resources) < len(resources):
            filtered_count = len(resources) - len(filtered_resources)
            response_parts.append(f"\n💡 已隐藏{filtered_count}条相似度较低的资源")
        
        return "\n".join(response_parts)
    
    def _filter_by_relevance(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根据相似度过滤资源，当相似度突然下跌时停止
        
        Args:
            resources: 资源列表
        
        Returns:
            过滤后的资源列表
        """
        if not resources:
            return []
        
        # 如果资源少于3个，不过滤
        if len(resources) < 3:
            return resources
        
        filtered_resources = []
        relevance_threshold = None
        
        for i, resource in enumerate(resources):
            relevance = resource.get("relevance", 0)
            
            # 第一个资源，记录基准相似度
            if i == 0:
                filtered_resources.append(resource)
                relevance_threshold = relevance * 0.6  # 设置阈值为第一个资源相似度的60%
                continue
            
            # 检查相似度是否突然下跌
            if i > 0:
                prev_relevance = resources[i-1].get("relevance", 0)
                
                # 如果相似度低于阈值，停止
                if relevance < relevance_threshold:
                    break
                
                # 如果相似度突然下跌超过40%，也停止（这是主要判断条件）
                drop_ratio = (prev_relevance - relevance) / prev_relevance
                if drop_ratio > 0.4:  # 下跌超过40%
                    break
            
            filtered_resources.append(resource)
        
        return filtered_resources
    
    def _process_resource_content(
        self, 
        category: str, 
        title: str, 
        content: str
    ) -> str:
        """
        处理资源内容
        
        Args:
            category: 资源分类
            title: 资源标题
            content: 原始内容
        
        Returns:
            处理后的内容
        """
        # 习题资源特殊处理
        if category == "习题资源":
            if "【图片题目】" in content:
                # 图片题目，显示文件名
                return "【图片题目】请查看题目文件"
            else:
                # 文字题目，显示完整内容
                return content[:200] + "..." if len(content) > 200 else content
        
        # 课件、课例、GGB只显示文件名
        if category in ["课件资源", "课例资源", "GGB资源"]:
            return "（请查看文件）"
        
        # 教案和教学大纲，返回完整内容（不再截断）
        if category in ["教案资源", "教学大纲"]:
            return content
        
        # 其他资源，生成摘要
        return self.content_processor.generate_summary(content, max_length=150)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"抱歉，响应生成过程中出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
    
    def _get_state_value(self, state: Any, key: str, default: Any = None) -> Any:
        """
        从状态对象中获取值（支持 MathAgentState 对象和字典）
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
            key: 键名
            default: 默认值
        
        Returns:
            对应的值
        """
        if hasattr(state, key):
            return getattr(state, key)
        elif isinstance(state, dict):
            return state.get(key, default)
        else:
            return default


# 向后兼容的函数接口
def response_formatting_node(state) -> Dict[str, Any]:
    """
    响应格式化节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含响应的更新状态
    """
    # 构建响应
    builder = ResponseBuilder()
    response = builder.build(state)
    
    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "messages": [{"role": "assistant", "content": response}]
    }
