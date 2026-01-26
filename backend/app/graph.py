from langgraph.graph import StateGraph, END, START
from .state import MathAgentState
from .nodes import (
    intent_understanding_node,
    resource_retrieval_node,
    lesson_plan_generation_node,
    visualization_suggestion_node,
    search_result_processing_node
)

def create_math_agent_graph():
    """
    创建高中数学资源智能体的LangGraph状态机
    """
    # 创建StateGraph实例
    graph = StateGraph(MathAgentState)
    
    # 添加节点
    graph.add_node("intent_understanding", intent_understanding_node)
    graph.add_node("resource_retrieval", resource_retrieval_node)
    graph.add_node("lesson_plan_generation", lesson_plan_generation_node)
    graph.add_node("visualization_suggestion", visualization_suggestion_node)
    graph.add_node("search_result_processing", search_result_processing_node)
    
    # 定义边和路由
    
    # 起始节点 -> 意图理解节点
    graph.add_edge(START, "intent_understanding")
    
    # 意图理解节点 -> 资源检索节点
    graph.add_edge("intent_understanding", "resource_retrieval")
    
    # 资源检索节点 -> 根据意图路由到不同处理节点
    def route_after_retrieval(state: MathAgentState):
        """
        根据意图路由到不同的处理节点
        """
        # 根据意图路由
        if state.intent == "generate_lesson_plan":
            return "lesson_plan_generation"
        elif state.intent == "visualization":
            return "visualization_suggestion"
        elif state.intent == "search":
            return "search_result_processing"
        else:
            # 默认路由到搜索结果处理
            return "search_result_processing"
    
    graph.add_conditional_edges(
        "resource_retrieval",
        route_after_retrieval,
        {
            "lesson_plan_generation": "lesson_plan_generation",
            "visualization_suggestion": "visualization_suggestion",
            "search_result_processing": "search_result_processing"
        }
    )
    
    # 处理节点 -> 结束节点
    graph.add_edge("lesson_plan_generation", END)
    graph.add_edge("visualization_suggestion", END)
    graph.add_edge("search_result_processing", END)
    
    # 编译图
    compiled_graph = graph.compile()
    
    return compiled_graph

# 导出图实例
math_agent_graph = create_math_agent_graph()
