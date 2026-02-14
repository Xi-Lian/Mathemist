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
    ResponseBuilder
)
from .state import MathAgentState


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
    retrieved_resources = retriever.retrieve(
        state.user_input,
        state.intent
    )
    
    return {
        "retrieved_resources": retrieved_resources,
        "current_step": "resource_retrieval",
        "error": None
    }


def lesson_plan_generation_node(state: MathAgentState) -> Dict[str, Any]:
    """
    教案生成节点
    根据用户需求和检索到的资源生成教案
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态，包含生成的教案
    """
    generator = LessonPlanGenerator()
    
    # 提取理论资源和教案示例
    theory_resources = state.retrieved_resources.get("theory_resources", [])
    lesson_plan_patterns = state.retrieved_resources.get("lesson_plan_patterns", [])
    
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
    visualization_examples = state.retrieved_resources.get("visualization_examples", [])
    
    suggestions = advisor.advise(
        state.user_input,
        visualization_examples
    )
    
    return {
        "visualization_suggestions": suggestions,
        "current_step": "visualization_suggestions",
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
    
    # 将 AI 消息添加到 messages 列表
    messages = state.messages if state.messages else []
    messages.append(ai_message)
    
    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "messages": messages,
        "message": ai_message
    }
