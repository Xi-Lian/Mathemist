"""
节点定义模块

职责：
- 定义LangGraph工作流的各个节点
- 协调各个核心模块完成工作流

依赖：
- app.core (核心功能模块)
- app.state (状态定义)
"""

import json
import uuid
from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from .core import (
    IntentAnalyzer,
    ResourceRetriever,
    LessonPlanGenerator,
    VisualizationAdvisor,
    ResponseBuilder,
    GGBDesignAdvisor,
)
from .core.unified_lesson_plan_system import unified_lesson_plan_system
from .search_agent_runtime import (
    build_search_response_payload,
    count_retrieved_resources,
    execute_search_tool_calls,
    get_empty_retrieved_resources,
    has_any_retrieved_resources,
    merge_retrieved_resources,
    normalize_query_inputs,
    retry_search_until_results,
)
from .state import MathAgentState

# 缓存核心实例，避免重复创建
_cached_retriever = None


def get_resource_retriever() -> ResourceRetriever:
    """
    获取资源检索器实例（单例模式）

    Returns:
        ResourceRetriever实例
    """
    global _cached_retriever
    if _cached_retriever is None:
        _cached_retriever = ResourceRetriever()
    return _cached_retriever


def _dict_to_langchain_message(message: Dict[str, Any]):
    message_type = message.get("type")
    content = message.get("content", "")
    message_id = message.get("id")

    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        content = "\n".join(part for part in text_parts if part)

    additional_kwargs: Dict[str, Any] = {}
    if message.get("tool_calls"):
        additional_kwargs["tool_calls"] = message.get("tool_calls")

    if message_type == "human":
        return HumanMessage(content=content, id=message_id)
    if message_type == "tool":
        return HumanMessage(content=content, id=message_id)
    return AIMessage(content=content, id=message_id, additional_kwargs=additional_kwargs)


def _collect_conversation_messages(state: MathAgentState) -> List:
    messages = []
    if getattr(state, "messages", None):
        for message in state.messages:
            if isinstance(message, dict):
                messages.append(_dict_to_langchain_message(message))
    elif getattr(state, "chat_history", None):
        for item in state.chat_history:
            role = item.get("role")
            content = item.get("content", "")
            if role == "user":
                messages.append(HumanMessage(content=content))
            else:
                messages.append(AIMessage(content=content))

    if not messages and getattr(state, "user_input", ""):
        messages.append(HumanMessage(content=state.user_input))

    return messages


def _messages_to_chat_history(messages: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    history: List[Dict[str, str]] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        message_type = message.get("type")
        if message_type not in {"human", "ai"}:
            continue

        content = message.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(part for part in text_parts if part)

        content = str(content or "").strip()
        if not content:
            continue

        role = "user" if message_type == "human" else "assistant"
        history.append({"role": role, "content": content})
    return history


def _generate_ai_reply(model: Any, system_prompt: str, conversation_messages: List, fallback: str) -> str:
    response = model.invoke([SystemMessage(content=system_prompt), *conversation_messages])
    content = (getattr(response, "content", "") or "").strip()
    return content or fallback


@tool
def search_resources_tool(
    query: str,
    resource_types: List[str] | None = None,
    queries: List[str] | None = None,
) -> str:
    """
    搜索本地数学资源库中的教案、习题、课件、课例、GGB 与教学大纲。
    当用户明确要查找、推荐、搜索现有资源时调用。
    可以同时提供 2-4 条语义等价或互补的查询表达，工具会逐条检索并合并结果。
    """
    retriever = get_resource_retriever()
    query_candidates = normalize_query_inputs(query, queries)
    print(f"🧠 search_resources_tool 收到多 query: {query_candidates}, resource_types={resource_types or []}")

    all_results: List[Dict[str, Any]] = []
    best_query = query
    best_count = -1

    for idx, candidate_query in enumerate(query_candidates, start=1):
        print(
            f"🔎 search_resources_tool 执行查询[{idx}/{len(query_candidates)}]: "
            f"{candidate_query!r}, resource_types={resource_types or []}"
        )
        candidate_resources = retriever.retrieve(
            query=candidate_query,
            intent="search",
            resource_types=resource_types or None,
        )
        if not isinstance(candidate_resources, dict):
            candidate_resources = get_empty_retrieved_resources()
        candidate_count = count_retrieved_resources(candidate_resources)
        print(f"   ↳ 查询[{idx}] 返回资源总数: {candidate_count}")
        all_results.append(candidate_resources)
        if candidate_count > best_count:
            best_query = candidate_query
            best_count = candidate_count
            print(f"   ✅ 查询[{idx}] 成为当前最佳结果")

    retrieved_resources = merge_retrieved_resources(all_results)
    formatted_response = build_search_response_payload(
        query=query,
        resource_types=resource_types,
        retrieved_resources=retrieved_resources if isinstance(retrieved_resources, dict) else get_empty_retrieved_resources(),
    )
    payload = {
        "query": best_query,
        "original_query": query,
        "queries": query_candidates,
        "resource_types": resource_types or [],
        "retrieved_resources": retrieved_resources,
        "formatted_response": formatted_response,
    }
    return json.dumps(payload, ensure_ascii=False)


def intent_understanding_node(state: MathAgentState) -> Dict[str, Any]:
    """
    意图理解节点
    分析用户输入，确定用户意图

    Args:
        state: 状态对象

    Returns:
        更新的状态，包含意图信息
    """
    print(f"\n{'=' * 80}")
    print("🧠 INTENT_UNDERSTANDING_NODE 被调用")
    print(f"{'=' * 80}")
    print(f"📝 用户输入：{state.user_input}")
    print(f"📚 state.messages 数量：{len(state.messages) if state.messages else 0}")
    print(
        f"📚 state.chat_history 数量：{len(state.chat_history) if state.chat_history else 0}"
    )
    print(f"📚 state.context: {state.context}")

    # 如果 messages 不为空，打印消息详情
    if state.messages:
        print(f"📋 state.messages 详情:")
        for i, msg in enumerate(state.messages[-5:]):  # 只打印最近 5 条
            msg_type = (
                msg.get("type", "unknown")
                if isinstance(msg, dict)
                else getattr(msg, "type", "unknown")
            )
            msg_id = (
                msg.get("id", "unknown")[:8]
                if isinstance(msg, dict)
                else getattr(msg, "id", "unknown")
            )
            print(f"   [{i}] type={msg_type}, id={msg_id}")

    analyzer = IntentAnalyzer()

    # 从 state.chat_history 获取对话历史（优先）
    chat_history = []
    if hasattr(state, "chat_history") and state.chat_history:
        chat_history = state.chat_history
    # 兼容：从 context 中获取 chat_history（备用）
    elif hasattr(state, "context") and state.context:
        chat_history = state.context.get("chat_history", [])
    elif isinstance(state, dict):
        chat_history = state.get("chat_history", []) or state.get("context", {}).get(
            "chat_history", []
        )
    elif hasattr(state, "messages") and state.messages:
        chat_history = _messages_to_chat_history(state.messages)

    if not chat_history and getattr(state, "messages", None):
        chat_history = _messages_to_chat_history(state.messages)

    print(f"📚 传递给 IntentAnalyzer 的 chat_history 数量：{len(chat_history)}")

    # 传递给 analyze 方法
    return analyzer.analyze(state.user_input, chat_history=chat_history)


def resource_retrieval_node(state: MathAgentState) -> Dict[str, Any]:
    """
    资源检索节点
    根据用户意图和输入检索相关资源

    Args:
        state: 状态对象

    Returns:
        更新的状态，包含检索到的资源
    """
    print(f"\n{'=' * 80}")
    print("🚀 RESOURCE_RETRIEVAL_NODE 被调用")
    print(f"{'=' * 80}")
    print(f"📝 用户输入: {state.user_input}")
    print(f"🎯 意图: {state.intent}")

    skip_retrieval = False
    if hasattr(state, 'skip_retrieval'):
        skip_retrieval = getattr(state, 'skip_retrieval', False)
    elif isinstance(state, dict):
        skip_retrieval = state.get('skip_retrieval', False)

    if skip_retrieval:
        print("⏭️ 当前输入为闲聊/非检索请求，跳过资源检索")
        return {
            "retrieved_resources": get_empty_retrieved_resources(),
            "current_step": "resource_retrieval",
            "error": None
        }
    
    retriever = get_resource_retriever()

    resource_types = None
    if hasattr(state, "resource_types"):
        resource_types = getattr(state, "resource_types", None)
    elif isinstance(state, dict):
        resource_types = state.get("resource_types", None)

    quantity_limit = None
    if hasattr(state, "quantity_limit"):
        quantity_limit = getattr(state, "quantity_limit", None)
    elif isinstance(state, dict):
        quantity_limit = state.get("quantity_limit", None)

    grade_info = None
    if hasattr(state, "grade_info"):
        grade_info = getattr(state, "grade_info", None)
    elif isinstance(state, dict):
        grade_info = state.get("grade_info", None)

    clarified_topic = None
    if hasattr(state, "clarified_topic"):
        clarified_topic = getattr(state, "clarified_topic", None)
    elif isinstance(state, dict):
        clarified_topic = state.get("clarified_topic", None)

    retrieved_resources = retriever.retrieve(
        query=state.user_input,
        intent=state.intent,
        resource_types=resource_types,
        quantity_limit=quantity_limit,
        grade_info=grade_info,
        clarified_topic=clarified_topic,
    )
    if not isinstance(retrieved_resources, dict):
        retrieved_resources = get_empty_retrieved_resources()

    return {
        "retrieved_resources": retrieved_resources,
        "current_step": "resource_retrieval",
        "error": None,
    }


def search_agent_node(state: MathAgentState) -> Dict[str, Any]:
    """
    搜索代理节点：
    - 由模型决定是否真的调用 search_resources_tool
    - 不再默认进入检索链路
    """
    print(f"\n{'=' * 80}")
    print("🛠️ SEARCH_AGENT_NODE 被调用")
    print(f"{'=' * 80}")
    print(f"📝 用户输入: {state.user_input}")

    model = IntentAnalyzer().model_config.get_model("intent")
    llm_with_tools = model.bind_tools([search_resources_tool])

    system_message = SystemMessage(
        content=(
            "你是高中数学资源助手。\n"
            "你的职责是先判断用户是否真的需要检索本地资源库。\n"
            "规则：\n"
            "1. 只有用户明确要找现成资源、教案、习题、课件、课例、GGB 或教学大纲时，才调用 search_resources_tool。\n"
            "2. 如果用户只是在打招呼、闲聊、确认、或者主题还很模糊，就直接对话，不要调用工具。\n"
            "3. 你必须结合当前对话历史理解省略信息。如果用户这轮没重复主题，但上文已经明确主题或资源类型，要先在脑中补全后再判断。\n"
            "4. 如果主题仍然不够明确，先反问确认需求，不要瞎搜。\n"
            "5. 如果调用了工具，必须提供一条主查询 query；当主查询可能不稳定时，再额外提供 1-3 条 queries 作为语义等价或互补表达。\n"
            "6. 这些 queries 必须由你根据语义理解自行生成，不要机械复制，也不要依赖固定模板。\n"
            "7. 多 query 的目标是覆盖不同自然表达，例如是否保留“的”、是否保留并列标点、是否用更完整的主题短语，但都必须忠实于用户原意。\n"
            "8. 如果调用了工具，优先使用工具返回的 formatted_response 直接回复，不要重复编造资源。\n"
            "9. 回复说人话，简洁。"
        )
    )

    conversation_messages = _collect_conversation_messages(state)
    model_response = llm_with_tools.invoke([system_message, *conversation_messages])

    tool_calls = getattr(model_response, "tool_calls", None) or []
    print(f"🧰 SEARCH_AGENT_NODE tool_calls 数量: {len(tool_calls)}")
    if not tool_calls:
        response_text = (getattr(model_response, "content", "") or "").strip()
        print(f"⚠️ SEARCH_AGENT_NODE 未调用工具，模型直接回复: {response_text[:300]}")
        if not response_text:
            response_text = "你先告诉我是想搜资源、生成教案，还是做可视化，我再继续。"
        return {
            "response": response_text,
            "response_mode": "conversation",
            "skip_retrieval": True,
            "current_step": "search_agent",
            "error": None,
            "intent": "conversation",
        }

    retrieved_resources, response_text, best_result_count, _ = retry_search_until_results(
        llm_with_tools=llm_with_tools,
        system_message=system_message,
        conversation_messages=conversation_messages,
        initial_tool_calls=tool_calls,
        search_tool=search_resources_tool,
        original_user_query=state.user_input,
        max_search_rounds=3,
    )

    print(f"📦 SEARCH_AGENT_NODE 最终选中资源总数: {count_retrieved_resources(retrieved_resources)}")

    if not has_any_retrieved_resources(retrieved_resources):
        print("⚠️ SEARCH_AGENT_NODE 最终判定为无检索结果，进入没找到兜底回复")
        response_text = _generate_ai_reply(
            model,
            (
                "你是高中数学资源助手。当前本地资源库没有找到可用结果。"
                "请结合对话历史，用自然中文告诉用户这次没搜到，并给出下一步建议，比如补充资源类型、年级、教材版本或更具体的主题。"
                "不要编造已找到的资源。"
            ),
            conversation_messages,
            "这次在本地资源库里没找到合适结果。你可以补充资源类型、年级或更具体的主题，我再帮你缩小范围。",
        )
    elif not response_text:
        print("ℹ️ SEARCH_AGENT_NODE 检索到结果，但 formatted_response 为空，进入简短说明回复")
        response_text = _generate_ai_reply(
            model,
            (
                "你是高中数学资源助手。用户已经通过工具获得了一批本地资源。"
                "请结合对话历史，用一句简洁的话说明你已经整理好了结果，并引导用户继续查看、筛选或补充条件。"
            ),
            conversation_messages,
            "我已经把相关资源整理好了。你可以继续补充条件，我再帮你筛得更准。",
        )

    return {
        "response": response_text,
        "response_mode": "agent_prebuilt",
        "retrieved_resources": retrieved_resources,
        "skip_retrieval": True,
        "current_step": "search_agent",
        "error": None,
        "intent": "search",
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
        state.user_input, session_id=state.lesson_plan_session_id
    )

    print(f"📝 统一教案系统结果: {result.get('status', 'unknown')}")

    # 构建返回的状态更新
    updates = {"current_step": "unified_lesson_plan", "error": None}

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
        state.user_input, theory_resources, lesson_plan_patterns
    )

    return {
        "lesson_plan": lesson_plan,
        "current_step": "lesson_plan_generation",
        "error": None,
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

    suggestions = advisor.advise(state.user_input, visualization_examples)

    return {
        "visualization_suggestions": suggestions,
        "current_step": "visualization_suggestions",
        "error": None,
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
            "error": "未找到相关GGB资源",
        }

    # 生成设计建议
    all_suggestions = []

    for ggb_resource in ggb_resources[:3]:  # 最多处理前3个GGB资源
        suggestion = advisor.generate_design_suggestions(
            chapter=ggb_resource.get("metadata", {}).get("章节", ""),
            textbook=ggb_resource.get("metadata", {}).get("教材", ""),
            ggb_filename=ggb_resource.get("title", ""),
            teaching_purpose=ggb_resource.get("content", ""),
            existing_steps=ggb_resource.get("metadata", {}).get("演示步骤", ""),
        )
        all_suggestions.append(suggestion)

    return {
        "ggb_design_suggestions": all_suggestions,
        "current_step": "ggb_design_advisor",
        "error": None,
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
    ai_message = {"type": "ai", "content": response, "id": f"msg_{uuid.uuid4().hex}"}

    if isinstance(state, dict):
        export_data = state.get("export_data")
        lesson_plan_session_id = state.get("lesson_plan_session_id")
    else:
        export_data = getattr(state, "export_data", None)
        lesson_plan_session_id = getattr(state, "lesson_plan_session_id", None)

    if export_data:
        ai_message["export_data"] = export_data

    # 将 AI 消息添加到 messages 列表
    # messages 会通过 reducer 自动合并，这里只需返回新增的消息

    # 更新 chat_history：保存用户输入和 AI 响应
    if isinstance(state, dict):
        chat_history = state.get("chat_history", []) or []
        user_input = state.get("user_input", "")
    else:
        chat_history = getattr(state, "chat_history", []) or []
        user_input = getattr(state, "user_input", "")
    chat_history = chat_history + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": response}
    ]

    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "messages": [ai_message],  # 只返回新消息，reducer 会自动合并
        "message": ai_message,
        "chat_history": chat_history,
        "lesson_plan_session_id": lesson_plan_session_id,
        "export_data": export_data,
    }
