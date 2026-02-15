from langgraph.graph import StateGraph, END, START
from .state import MathAgentState

def create_math_agent_graph():
    """
    创建高中数学资源智能体的LangGraph状态机
    """
    # 动态导入节点函数，确保使用最新的代码
    from .nodes import (
        intent_understanding_node,
        resource_retrieval_node,
        lesson_plan_generation_node,
        visualization_suggestions_node,
        ggb_design_advisor_node,
        response_formatting_node
    )
    
    # 创建StateGraph实例
    graph = StateGraph(MathAgentState)
    
    # 添加节点
    graph.add_node("intent_understanding", intent_understanding_node)
    graph.add_node("resource_retrieval", resource_retrieval_node)
    graph.add_node("lesson_plan_generation", lesson_plan_generation_node)
    graph.add_node("visualization_suggestions", visualization_suggestions_node)
    graph.add_node("ggb_design_advisor", ggb_design_advisor_node)
    graph.add_node("response_formatting", response_formatting_node)
    
    # 定义边和路由
    
    # 起始节点 -> 意图理解节点
    graph.add_edge(START, "intent_understanding")
    
    # 意图理解节点 -> 资源检索节点
    graph.add_edge("intent_understanding", "resource_retrieval")
    
    # 资源检索节点 -> 根据意图路由到不同处理节点
    def route_after_retrieval(state):
        """
        根据意图路由到不同的处理节点
        """
        # 处理 state 可能是字典或 MathAgentState 对象的情况
        if isinstance(state, dict):
            intent = state.get("intent")
            intents = state.get("intents", [])
            retrieved_resources = state.get("retrieved_resources", {})
            resource_types = state.get("resource_types", [])
        else:
            intent = getattr(state, "intent", None)
            intents = getattr(state, "intents", [])
            retrieved_resources = getattr(state, "retrieved_resources", {})
            resource_types = getattr(state, "resource_types", [])
        
        print(f"🔀 路由函数: state 类型 = {type(state)}")
        print(f"🔀 路由函数: intent = {intent}")
        print(f"🔀 路由函数: intents = {intents}")
        print(f"🔀 路由函数: resource_types = {resource_types}")
        
        # 如果用户明确指定了资源类型，直接跳到响应格式化
        if resource_types:
            print(f"🔀 用户明确指定了资源类型，直接跳到响应格式化")
            return "response_formatting"
        
        # 检查是否有GGB资源，如果有，优先生成GGB设计建议
        ggb_resources = retrieved_resources.get("ggb_resources", [])
        if ggb_resources:
            print(f"🔀 检测到GGB资源: {len(ggb_resources)}个，路由到GGB设计建议节点")
            return "ggb_design_advisor"
        
        # 检查是否有多个高置信度意图
        high_confidence_intents = [i for i in intents if i.get("confidence", 0) > 0.6]
        
        if len(high_confidence_intents) > 1:
            print(f"🔀 检测到多个高置信度意图: {high_confidence_intents}")
            # 优先处理教案生成意图
            if any(i.get("type") == "generate_lesson_plan" for i in high_confidence_intents):
                return "lesson_plan_generation"
            # 其次处理可视化意图
            elif any(i.get("type") == "visualization" for i in high_confidence_intents):
                return "visualization_suggestions"
        
        # 根据主要意图路由
        if intent == "generate_lesson_plan":
            return "lesson_plan_generation"
        elif intent == "visualization":
            return "visualization_suggestions"
        elif intent == "search":
            # 搜索意图直接跳到响应格式化
            return "response_formatting"
        else:
            # 默认路由到响应格式化
            print(f"⚠️ 未知意图 {intent}，使用默认路由")
            return "response_formatting"
    
    graph.add_conditional_edges(
        "resource_retrieval",
        route_after_retrieval,
        {
            "lesson_plan_generation": "lesson_plan_generation",
            "visualization_suggestions": "visualization_suggestions",
            "ggb_design_advisor": "ggb_design_advisor",
            "response_formatting": "response_formatting"
        }
    )
    
    # 所有处理节点 -> 响应格式化节点
    graph.add_edge("lesson_plan_generation", "response_formatting")
    graph.add_edge("visualization_suggestions", "response_formatting")
    graph.add_edge("ggb_design_advisor", "response_formatting")
    
    # 响应格式化节点 -> 结束节点
    graph.add_edge("response_formatting", END)
    
    # 编译图
    compiled_graph = graph.compile()
    
    return compiled_graph
