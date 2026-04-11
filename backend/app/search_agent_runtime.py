import json
from typing import Any, Callable, Dict, List, Tuple

from langchain_core.messages import HumanMessage

from .core import ResponseBuilder


def get_empty_retrieved_resources() -> Dict[str, Any]:
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


def has_any_retrieved_resources(retrieved_resources: Dict[str, Any]) -> bool:
    if not isinstance(retrieved_resources, dict):
        return False
    for value in retrieved_resources.values():
        if isinstance(value, list) and value:
            return True
    return False


def count_retrieved_resources(retrieved_resources: Dict[str, Any]) -> int:
    if not isinstance(retrieved_resources, dict):
        return 0
    total = 0
    for value in retrieved_resources.values():
        if isinstance(value, list):
            total += len(value)
    return total


def normalize_query_inputs(query: str, queries: List[str] | None = None) -> List[str]:
    merged_queries: List[str] = []
    for item in [query, *(queries or [])]:
        cleaned = str(item or "").strip().strip("，,。；;！!？? ")
        if cleaned and cleaned not in merged_queries:
            merged_queries.append(cleaned)
    return merged_queries


def resource_identity(resource: Dict[str, Any]) -> str:
    if not isinstance(resource, dict):
        return ""
    return " | ".join(
        str(resource.get(key, "") or "")
        for key in ("title", "source", "filename", "question", "answer")
    )


def merge_retrieved_resources(resource_groups: List[Dict[str, Any]]) -> Dict[str, Any]:
    merged = get_empty_retrieved_resources()
    if not resource_groups:
        return merged

    for group in resource_groups:
        if not isinstance(group, dict):
            continue
        for key, value in group.items():
            if key not in merged or not isinstance(value, list):
                continue
            existing = merged[key]
            seen = {resource_identity(item) for item in existing if isinstance(item, dict)}
            for item in value:
                identity = resource_identity(item) if isinstance(item, dict) else ""
                if identity and identity in seen:
                    continue
                if identity:
                    seen.add(identity)
                existing.append(item)
    return merged


def build_search_response_payload(
    query: str,
    resource_types: List[str] | None,
    retrieved_resources: Dict[str, Any],
) -> str:
    builder = ResponseBuilder()
    return builder._build_search_response(
        {
            "intent": "search",
            "user_input": query,
            "resource_types": resource_types or [],
            "retrieved_resources": retrieved_resources,
        }
    )


def execute_search_tool_calls(
    tool_calls: List[Dict[str, Any]],
    search_tool: Any,
    original_user_query: str | None = None,
) -> Tuple[Dict[str, Any], str, int, List[str]]:
    retrieved_resources = get_empty_retrieved_resources()
    response_text = ""
    best_result_count = -1
    attempted_queries: List[str] = []

    for idx, tool_call in enumerate(tool_calls, start=1):
        if tool_call.get("name") != search_tool.name:
            print(f"⚠️ 跳过未知工具调用[{idx}]: {tool_call.get('name')}")
            continue
        tool_args = tool_call.get("args", {}) or {}
        attempted_queries.extend(normalize_query_inputs(tool_args.get("query", ""), tool_args.get("queries", [])))
        print(
            f"🔍 执行工具调用[{idx}]: "
            f"query={tool_args.get('query', '')!r}, queries={tool_args.get('queries', [])}, "
            f"resource_types={tool_args.get('resource_types', [])}"
        )
        tool_result = search_tool.invoke(tool_args)
        try:
            parsed = json.loads(tool_result)
        except Exception:
            parsed = {}
        if isinstance(parsed, dict):
            candidate_resources = parsed.get("retrieved_resources")
            candidate_count = count_retrieved_resources(candidate_resources)
            print(f"   ↳ 工具调用[{idx}] 返回资源总数: {candidate_count}")
            if candidate_count > best_result_count:
                best_result_count = candidate_count
                print(f"   ✅ 工具调用[{idx}] 成为当前最佳结果")
                if isinstance(candidate_resources, dict):
                    retrieved_resources = candidate_resources
                    response_text = build_search_response_payload(
                        query=original_user_query or tool_args.get("query", "") or "",
                        resource_types=tool_args.get("resource_types", []),
                        retrieved_resources=candidate_resources,
                    ).strip()
            else:
                print(f"   ℹ️ 工具调用[{idx}] 未超过当前最佳结果数 {best_result_count}")

    return retrieved_resources, response_text, best_result_count, attempted_queries


def retry_search_until_results(
    llm_with_tools: Any,
    system_message: Any,
    conversation_messages: List[Any],
    initial_tool_calls: List[Dict[str, Any]],
    search_tool: Any,
    original_user_query: str,
    max_search_rounds: int = 3,
) -> Tuple[Dict[str, Any], str, int, List[str]]:
    retrieved_resources, response_text, best_result_count, attempted_queries = execute_search_tool_calls(
        initial_tool_calls,
        search_tool=search_tool,
        original_user_query=original_user_query,
    )

    current_round = 1
    while not has_any_retrieved_resources(retrieved_resources) and current_round < max_search_rounds:
        next_round = current_round + 1
        unique_attempted = []
        seen_queries = set()
        for query in attempted_queries:
            if query and query not in seen_queries:
                seen_queries.add(query)
                unique_attempted.append(query)

        print(f"🔁 SEARCH_AGENT_NODE 第{current_round}轮检索为空，发起第{next_round}轮多 query 重试")
        retry_message = HumanMessage(
            content=(
                f"前 {current_round} 轮 search_resources_tool 检索都没有拿到结果。\n"
                f"原始用户请求：{original_user_query}\n"
                f"之前已经尝试过的 query：{unique_attempted}\n"
                "请重新判断是否需要再次调用 search_resources_tool。\n"
                "如果再次调用，必须保留用户原始语义，并提供 2-4 条新的互补 queries。\n"
                "新的 queries 要尽量避免与上面已经试过的重复，优先覆盖更完整主题、自然中文表达、不同短语组合。\n"
                "不要直接回答“没找到”，先完成这一轮重试。"
            )
        )
        retry_response = llm_with_tools.invoke([system_message, *conversation_messages, retry_message])
        retry_tool_calls = getattr(retry_response, "tool_calls", None) or []
        print(f"🧰 SEARCH_AGENT_NODE 第{next_round}轮重试 tool_calls 数量: {len(retry_tool_calls)}")
        if not retry_tool_calls:
            break

        retry_resources, retry_response_text, retry_best_result_count, retry_attempted_queries = execute_search_tool_calls(
            retry_tool_calls,
            search_tool=search_tool,
            original_user_query=original_user_query,
        )
        attempted_queries.extend(retry_attempted_queries)
        if retry_best_result_count > best_result_count:
            best_result_count = retry_best_result_count
            retrieved_resources = retry_resources
            response_text = retry_response_text
        current_round = next_round

    return retrieved_resources, response_text, best_result_count, attempted_queries
