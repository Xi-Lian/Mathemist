from langgraph.graph import StateGraph, END, START
from .state import MathAgentState

def create_math_agent_graph():
    """
    创建高中数学资源智能体的LangGraph状态机
    支持多意图处理
    """
    # 动态导入节点函数，确保使用最新的代码
    from .nodes import (
        intent_understanding_node,
        resource_retrieval_node,
        unified_lesson_plan_node,
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
    graph.add_node("unified_lesson_plan", unified_lesson_plan_node)
    graph.add_node("lesson_plan_generation", lesson_plan_generation_node)
    graph.add_node("visualization_suggestions", visualization_suggestions_node)
    graph.add_node("ggb_design_advisor", ggb_design_advisor_node)
    graph.add_node("multi_intent_processor", multi_intent_processor_node)
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
            lesson_plan_session_id = state.get("lesson_plan_session_id")
            user_input = state.get("user_input", "")
        else:
            intent = getattr(state, "intent", None)
            intents = getattr(state, "intents", [])
            retrieved_resources = getattr(state, "retrieved_resources", {})
            resource_types = getattr(state, "resource_types", [])
            lesson_plan_session_id = getattr(state, "lesson_plan_session_id", None)
            user_input = getattr(state, "user_input", "")

        # 兜底：防止检索阶段返回 None 导致后续 .get 崩溃
        if not isinstance(retrieved_resources, dict):
            retrieved_resources = {}
        
        print(f"🔀 路由函数: state 类型 = {type(state)}")
        print(f"🔀 路由函数: intent = {intent}")
        print(f"🔀 路由函数: intents = {intents}")
        print(f"🔀 路由函数: resource_types = {resource_types}")
        print(f"🔀 路由函数: lesson_plan_session_id = {lesson_plan_session_id}")
        
        # 检查指令词，避免生成教案和推送资源的场景混淆
        resource_retrieval_keywords = ["推送", "给", "找", "推荐", "有没有", "我要", "帮我找", "想要", "需要"]
        has_resource_retrieval = any(keyword in user_input for keyword in resource_retrieval_keywords)
        
        print(f"🔀 包含资源获取指令词: {has_resource_retrieval}")
        print(f"🔀 用户输入: {user_input}")
        print(f"🔀 输入类型: {type(user_input)}")
        
        # 检查是否为"查看完整教案"请求或修改意见
        if isinstance(user_input, str):
            normalized_input = user_input.replace(' ', '')  # 移除所有空格
            print(f"🔀 归一化输入: {normalized_input}")
            print(f"🔀 包含'查看完整教案': {'查看完整教案' in normalized_input}")
            print(f"包含'完整教案': {'完整教案' in normalized_input}")
            if "查看完整教案" in normalized_input or "完整教案" in normalized_input:
                print(f"🔀 检测到'查看完整教案'请求，路由到统一教案节点")
                return "unified_lesson_plan"
            
            # 检查是否为修改意见
            revision_keywords = [
                # 表达不满意或需要修改
                "觉得", "感觉", "认为", "希望", "想要", "需要", "应该", "建议", "提议",
                # 具体修改动作
                "修改", "调整", "改进", "完善", "优化", "补充", "增加", "添加", "减少", "删除", "删除掉",
                # 疑问式修改请求
                "能不能", "能否", "可不可以", "是否可以", "能不能够",
                # 具体修改内容
                "太短", "太长", "太简单", "太复杂", "不够", "不足", "缺少", "缺乏",
                # 其他修改相关词汇
                "改一下", "改改", "调整一下", "完善一下", "优化一下", "补充一下"
            ]
            has_revision_request = any(keyword in user_input for keyword in revision_keywords)
            if has_revision_request:
                print(f"🔀 检测到修改意见，路由到统一教案节点（无论是否有session_id）")
                return "unified_lesson_plan"
        else:
            print(f"⚠️ 用户输入不是字符串: {user_input}")
        
        # 检查是否有多个高置信度意图
        high_confidence_intents = [i for i in intents if i.get("confidence", 0) > 0.6]
        
        if len(high_confidence_intents) > 1:
            print(f"🔀 检测到多个高置信度意图: {high_confidence_intents}")
            # 有多个意图，使用多意图处理器
            return "multi_intent_processor"
        
        # 如果包含资源获取指令词，强制使用响应格式化，不生成教案
        if has_resource_retrieval:
            print(f"🔀 检测到资源获取指令词，强制使用响应格式化，不生成教案")
            return "response_formatting"
        
        # 如果用户明确指定了资源类型，检查是否是教案生成意图
        if resource_types:
            print(f"🔀 检测到资源类型: {resource_types}")
            if intent == "generate_lesson_plan" or any(i.get("type") == "generate_lesson_plan" for i in intents):
                print(f"🔀 检测到教案生成意图，继续走统一教案流程")
                return "unified_lesson_plan"
            else:
                print(f"🔀 非教案生成资源类型，直接跳到响应格式化")
                return "response_formatting"
        
        # 检查是否有GGB资源，如果有，优先生成GGB设计建议
        ggb_resources = retrieved_resources.get("ggb_resources", [])
        if ggb_resources:
            print(f"🔀 检测到GGB资源: {len(ggb_resources)}个，路由到GGB设计建议节点")
            return "ggb_design_advisor"
        
        # 根据主要意图路由
        if intent == "generate_lesson_plan":
            return "unified_lesson_plan"
        elif intent == "visualization":
            return "visualization_suggestions"
        elif intent == "search":
            return "response_formatting"
        else:
            print(f"⚠️ 未知意图 {intent}，使用默认路由")
            return "response_formatting"
    
    graph.add_conditional_edges(
        "resource_retrieval",
        route_after_retrieval,
        {
            "unified_lesson_plan": "unified_lesson_plan",
            "lesson_plan_generation": "lesson_plan_generation",
            "visualization_suggestions": "visualization_suggestions",
            "ggb_design_advisor": "ggb_design_advisor",
            "multi_intent_processor": "multi_intent_processor",
            "response_formatting": "response_formatting"
        }
    )
    
    # 统一教案节点 -> 检查是否需要响应格式化
    def route_after_unified_lesson_plan(state):
        """
        统一教案处理后的路由
        """
        if isinstance(state, dict):
            response = state.get("response")
        else:
            response = getattr(state, "response", None)
        
        if response:
            print(f"🔀 统一教案已生成响应，直接结束")
            return "response_formatting"
        
        return "response_formatting"
    
    graph.add_conditional_edges(
        "unified_lesson_plan",
        route_after_unified_lesson_plan,
        {
            "response_formatting": "response_formatting"
        }
    )
    
    # 多意图处理器 -> 响应格式化
    graph.add_edge("multi_intent_processor", "response_formatting")
    
    # 所有处理节点 -> 响应格式化节点
    graph.add_edge("lesson_plan_generation", "response_formatting")
    graph.add_edge("visualization_suggestions", "response_formatting")
    graph.add_edge("ggb_design_advisor", "response_formatting")
    
    # 响应格式化节点 -> 结束节点
    graph.add_edge("response_formatting", END)
    
    # 编译图
    compiled_graph = graph.compile()
    
    return compiled_graph


def multi_intent_processor_node(state) -> dict:
    """
    多意图处理器节点
    同时处理多个高置信度意图
    
    Args:
        state: 状态对象
    
    Returns:
        更新的状态
    """
    from .nodes import (
        unified_lesson_plan_node,
        visualization_suggestions_node,
        ggb_design_advisor_node
    )
    
    print(f"\n🔄 多意图处理器启动")
    
    # 获取高置信度意图
    if isinstance(state, dict):
        intents = state.get("intents", [])
    else:
        intents = getattr(state, "intents", [])
    
    high_confidence_intents = [i for i in intents if i.get("confidence", 0) > 0.6]
    print(f"🎯 待处理的高置信度意图: {high_confidence_intents}")
    
    updates = {
        "current_step": "multi_intent_processor",
        "error": None,
        "processed_intents": []
    }
    
    # 按优先级处理各个意图
    intent_types = [i.get("type") for i in high_confidence_intents]
    
    # 1. 处理教案生成意图
    if "generate_lesson_plan" in intent_types:
        print(f"📝 处理教案生成意图")
        lesson_plan_result = unified_lesson_plan_node(state)
        updates.update(lesson_plan_result)
        updates["processed_intents"].append("generate_lesson_plan")
    
    # 2. 处理可视化意图
    if "visualization" in intent_types:
        print(f"🎨 处理可视化意图")
        viz_result = visualization_suggestions_node(state)
        updates.update(viz_result)
        updates["processed_intents"].append("visualization")
    
    # 3. 检查是否有GGB资源并处理
    if isinstance(state, dict):
        retrieved_resources = state.get("retrieved_resources", {})
    else:
        retrieved_resources = getattr(state, "retrieved_resources", {})

    # 兜底：防止检索阶段返回 None 导致后续 .get 崩溃
    if not isinstance(retrieved_resources, dict):
        retrieved_resources = {}
    
    ggb_resources = retrieved_resources.get("ggb_resources", [])
    if ggb_resources and "visualization" in intent_types:
        print(f"🔧 处理GGB设计建议")
        ggb_result = ggb_design_advisor_node(state)
        updates.update(ggb_result)
        updates["processed_intents"].append("ggb_design")
    
    print(f"✅ 多意图处理完成，已处理: {updates['processed_intents']}")
    
    return updates
