"""
节点定义模块

职责：
- 定义LangGraph工作流的各个节点
- 协调各个核心模块完成工作流

依赖：
- app.core (核心功能模块)
- app.state (状态定义)
"""

import uuid
from typing import Dict, Any
from .core import (
    IntentAnalyzer,
    ResourceRetriever,
    LessonPlanGenerator,
    VisualizationAdvisor,
    ResponseBuilder,
    GGBDesignAdvisor
)
from .core.unified_lesson_plan_system import unified_lesson_plan_system
from .state import MathAgentState


def _get_empty_retrieved_resources() -> Dict[str, Any]:
    """统一的空检索结果结构，避免 None 传播到下游节点。"""
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
    }


def intent_understanding_node(state: MathAgentState) -> Dict[str, Any]:
    """
    意图理解节点
    分析用户输入，确定用户意图
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含意图信息
    """
    analyzer = IntentAnalyzer()
    return analyzer.analyze(state.user_input)


def resource_retrieval_node(state: MathAgentState) -> Dict[str, Any]:
    """
    资源检索节点
    根据用户意图和输入检索相关资源
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含检索到的资源
    """
    retriever = ResourceRetriever()
    
    # 获取资源类型（如果用户明确指定了）
    resource_types = None
    if hasattr(state, 'resource_types'):
        resource_types = getattr(state, 'resource_types', None)
    elif isinstance(state, dict):
        resource_types = state.get('resource_types', None)
    
    # 如果用户没有明确指定资源类型，但意图是搜索，则检索所有类型
    # 如果用户明确指定了资源类型，则只检索指定类型
    retrieved_resources = retriever.retrieve(
        state.user_input,
        state.intent,
        resource_types=resource_types
    )
    if not isinstance(retrieved_resources, dict):
        retrieved_resources = _get_empty_retrieved_resources()
    
    return {
        "retrieved_resources": retrieved_resources,
        "current_step": "resource_retrieval",
        "error": None
    }


def unified_lesson_plan_node(state: MathAgentState) -> Dict[str, Any]:
    """
    统一教案生成节点
    智能判断用户输入完整度，自动选择生成或引导方式
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态
    """
    print(f"\n📝 统一教案生成节点启动")
    print(f"📝 用户输入: {state.user_input}")
    print(f"📝 现有会话ID: {state.lesson_plan_session_id}")
    
    # 调用统一教案系统
    result = unified_lesson_plan_system.process_lesson_plan_request(
        state.user_input,
        session_id=state.lesson_plan_session_id
    )
    
    print(f"📝 统一教案系统结果: {result.get('status', 'unknown')}")
    
    # 构建返回的状态更新
    updates = {
        "current_step": "unified_lesson_plan",
        "error": None
    }
    
    if result.get("success"):
        updates["lesson_plan_session_id"] = result.get("session_id")
        updates["lesson_plan_status"] = result.get("status")
        updates["lesson_plan_collected_info"] = result.get("collected_info")
        updates["response"] = result.get("response")
        if "export_data" in result and result.get("export_data"):
            updates["export_data"] = result.get("export_data")
        
        if result.get("status") == "completed" and "lesson_plan" in result:
            updates["lesson_plan"] = result.get("lesson_plan")
    else:
        updates["error"] = result.get("error")
        updates["response"] = f"抱歉，教案生成过程中出现问题：{result.get('error')}"
    
    return updates


def lesson_plan_generation_node(state: MathAgentState) -> Dict[str, Any]:
    """
    教案生成节点（向后兼容）
    根据用户需求和检索到的资源生成教案
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含生成的教案
    """
    generator = LessonPlanGenerator()
    
    # 提取理论资源和教案示例
    retrieved_resources = state.retrieved_resources or {}
    theory_resources = retrieved_resources.get("theory_resources", [])
    lesson_plan_patterns = retrieved_resources.get("lesson_plan_patterns", [])
    
    lesson_plan = generator.generate(
        state.user_input,
        theory_resources,
        lesson_plan_patterns
    )
    
    return {
        "lesson_plan": lesson_plan,
        "current_step": "lesson_plan_generation",
        "error": None
    }


def visualization_suggestions_node(state: MathAgentState) -> Dict[str, Any]:
    """
    可视化建议节点
    根据用户需求和检索到的示例生成可视化建议
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含可视化建议
    """
    advisor = VisualizationAdvisor()
    
    # 提取可视化示例
    retrieved_resources = state.retrieved_resources or {}
    visualization_examples = retrieved_resources.get("visualization_examples", [])
    
    suggestions = advisor.advise(
        state.user_input,
        visualization_examples
    )
    
    return {
        "visualization_suggestions": suggestions,
        "current_step": "visualization_suggestions",
        "error": None
    }


def ggb_design_advisor_node(state: MathAgentState) -> Dict[str, Any]:
    """
    GGB设计建议节点
    根据检索到的GGB资源生成GeoGebra动态图设计建议
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含GGB设计建议
    """
    advisor = GGBDesignAdvisor()
    
    # 提取GGB资源
    retrieved_resources = state.retrieved_resources or {}
    ggb_resources = retrieved_resources.get("ggb", [])
    
    # 如果没有GGB资源，返回空结果
    if not ggb_resources:
        return {
            "ggb_design_suggestions": None,
            "current_step": "ggb_design_advisor",
            "error": "未找到相关GGB资源"
        }
    
    # 生成设计建议
    all_suggestions = []
    
    for ggb_resource in ggb_resources[:3]:  # 最多处理前3个GGB资源
        suggestion = advisor.generate_design_suggestions(
            chapter=ggb_resource.get('metadata', {}).get('章节', ''),
            textbook=ggb_resource.get('metadata', {}).get('教材', ''),
            ggb_filename=ggb_resource.get('title', ''),
            teaching_purpose=ggb_resource.get('content', ''),
            existing_steps=ggb_resource.get('metadata', {}).get('演示步骤', '')
        )
        all_suggestions.append(suggestion)
    
    return {
        "ggb_design_suggestions": all_suggestions,
        "current_step": "ggb_design_advisor",
        "error": None
    }


def response_formatting_node(state: MathAgentState) -> Dict[str, Any]:
    """
    响应格式化节点
    根据意图和生成的结果构建最终响应
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含格式化的响应
    """
    builder = ResponseBuilder()
    response = builder.build(state)
    
    # 创建 AI 消息
    ai_message = {
        "type": "ai",
        "content": response,
        "id": f"msg_{uuid.uuid4().hex}"
    }

    if isinstance(state, dict):
        export_data = state.get("export_data")
        lesson_plan_session_id = state.get("lesson_plan_session_id")
    else:
        export_data = getattr(state, "export_data", None)
        lesson_plan_session_id = getattr(state, "lesson_plan_session_id", None)

    if export_data:
        ai_message["export_data"] = export_data
    
    # 将 AI 消息添加到 messages 列表
    messages = state.messages if state.messages else []
    messages.append(ai_message)
    
    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "messages": messages,
        "message": ai_message,
        "lesson_plan_session_id": lesson_plan_session_id,
        "export_data": export_data,
    }
