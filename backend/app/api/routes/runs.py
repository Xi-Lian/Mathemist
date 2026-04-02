"""
运行相关路由模块

职责：
- 处理运行相关的API请求
- 提供运行创建、查询、流式接口
- 支持运行与用户关联

依赖：
- fastapi
- app.api.models (数据模型)
- app.utils (工具函数)
- app.graph (图实例)
- app.api.routes.threads (线程存储)
- app.core.user_system (用户系统)
"""

import json
import logging
import os
import time
import uuid
from typing import Dict, Any, AsyncGenerator, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from fastapi.responses import StreamingResponse
from app.api.models import Run, RunCreateRequest, RunWithUser
from app.utils import generate_id, get_current_timestamp, CustomJSONEncoder
from app.graph import create_math_agent_graph
from app.api.routes import threads as threads_module
from app.core.user_system import user_system

logger = logging.getLogger(__name__)

router = APIRouter()

# 内存存储运行（生产环境应该使用数据库）
runs: Dict[str, Dict[str, Any]] = {}
# 使用 threads 模块中的 threads 字典
threads = threads_module.threads

RUN_STREAM_LOG_MODE = os.getenv("RUN_STREAM_LOG_MODE", "summary").strip().lower()
RUN_STREAM_LOG_EVERY_N = max(1, int(os.getenv("RUN_STREAM_LOG_EVERY_N", "50")))
RUN_STREAM_PREVIEW_CHARS = max(40, int(os.getenv("RUN_STREAM_PREVIEW_CHARS", "180")))


def _shorten_text(value: Any, max_chars: int = RUN_STREAM_PREVIEW_CHARS) -> str:
    text = "" if value is None else str(value)
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...(len={len(text)})"


def _safe_message_preview(message: Dict[str, Any]) -> Dict[str, Any]:
    content = message.get("content", "")
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        content = " ".join(text_parts)
    return {
        "id": message.get("id"),
        "type": message.get("type"),
        "content_preview": _shorten_text(content),
    }


def _summarize_input_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    messages = payload.get("messages")
    message_count = len(messages) if isinstance(messages, list) else 0
    last_message = messages[-1] if message_count else None

    summary = {
        "keys": sorted(list(payload.keys())),
        "message_count": message_count,
    }
    if isinstance(last_message, dict):
        summary["last_message"] = _safe_message_preview(last_message)
    if "user_input" in payload:
        summary["user_input_preview"] = _shorten_text(payload.get("user_input"))
    return summary


def _summarize_node_output(node_output: Any) -> Dict[str, Any]:
    if not isinstance(node_output, dict):
        return {
            "type": type(node_output).__name__,
            "preview": _shorten_text(node_output),
        }

    summary: Dict[str, Any] = {"keys": sorted(list(node_output.keys()))}

    messages = node_output.get("messages")
    if isinstance(messages, list):
        summary["messages_count"] = len(messages)

    response = node_output.get("response")
    if isinstance(response, str):
        summary["response_preview"] = _shorten_text(response)

    current_step = node_output.get("current_step")
    if current_step:
        summary["current_step"] = current_step

    error = node_output.get("error")
    if error:
        summary["error_preview"] = _shorten_text(error)

    return summary


def _summarize_messages_event(data: Any) -> Dict[str, Any]:
    first = None
    metadata = None

    if isinstance(data, (list, tuple)) and len(data) == 2:
        first, metadata = data
    elif isinstance(data, list):
        first = data[0] if data else None
    else:
        first = data

    summary: Dict[str, Any] = {
        "type": type(first).__name__ if first is not None else type(data).__name__
    }

    if isinstance(first, dict):
        summary["message"] = _safe_message_preview(first)
    else:
        content = getattr(first, "content", "")
        response_metadata = getattr(first, "response_metadata", {}) or {}
        usage_metadata = getattr(first, "usage_metadata", {}) or {}
        summary["message"] = {
            "id": getattr(first, "id", None),
            "content_preview": _shorten_text(content),
        }
        if response_metadata.get("model_name"):
            summary["message"]["model_name"] = response_metadata.get("model_name")
        if response_metadata.get("finish_reason"):
            summary["message"]["finish_reason"] = response_metadata.get("finish_reason")
        if usage_metadata:
            summary["message"]["has_usage"] = True

    if isinstance(metadata, dict):
        for key in ("langgraph_node", "langgraph_step"):
            if key in metadata:
                summary[key] = metadata[key]

    finish_reason = None
    if isinstance(first, dict):
        finish_reason = (first.get("response_metadata") or {}).get("finish_reason")
    else:
        finish_reason = getattr(first, "response_metadata", {}) or {}
        finish_reason = finish_reason.get("finish_reason")

    summary["is_final"] = bool(finish_reason)
    return summary


def _elapsed_ms(start_time: float) -> int:
    return int((time.perf_counter() - start_time) * 1000)


def _message_id(message: Any) -> Optional[str]:
    if isinstance(message, dict):
        return message.get("id")
    return getattr(message, "id", None)


def _merge_message_lists(existing: Any, incoming: Any) -> list[Any]:
    existing_list = list(existing) if isinstance(existing, list) else []
    incoming_list = list(incoming) if isinstance(incoming, list) else []

    if not existing_list:
        return incoming_list
    if not incoming_list:
        return existing_list

    merged = list(existing_list)
    index_by_id: Dict[str, int] = {}
    for idx, message in enumerate(merged):
        message_id = _message_id(message)
        if message_id:
            index_by_id[message_id] = idx

    for message in incoming_list:
        message_id = _message_id(message)
        if message_id and message_id in index_by_id:
            merged[index_by_id[message_id]] = message
            continue
        merged.append(message)
        if message_id:
            index_by_id[message_id] = len(merged) - 1

    return merged


def _format_stage_timings(node_finish_times: Dict[str, int]) -> Dict[str, int]:
    stage_durations: Dict[str, int] = {}
    previous_ms = 0
    for node_name, finished_ms in node_finish_times.items():
        stage_durations[node_name] = finished_ms - previous_ms
        previous_ms = finished_ms
    return stage_durations


def _log_stream_timing_summary(
    *,
    total_ms: int,
    first_update_ms: Optional[int],
    first_message_ms: Optional[int],
    final_message_ms: Optional[int],
    chunk_count: int,
    node_finish_times: Dict[str, int],
    node_update_counts: Dict[str, int],
) -> None:
    stage_durations = _format_stage_timings(node_finish_times)
    final_output_ms = final_message_ms if final_message_ms is not None else total_ms
    generation_window_ms = (
        final_output_ms - first_message_ms if first_message_ms is not None else None
    )

    logger.info("⏱️ 流式耗时汇总")
    logger.info(
        "  total_ms=%s, first_update_ms=%s, first_message_ms=%s, final_message_ms=%s, chunks=%s",
        total_ms,
        first_update_ms,
        first_message_ms,
        final_message_ms,
        chunk_count,
    )
    logger.info(
        "  node_finish_ms=%s",
        node_finish_times,
    )
    logger.info(
        "  node_stage_ms=%s",
        stage_durations,
    )
    logger.info(
        "  node_updates=%s, generation_window_ms=%s",
        node_update_counts,
        generation_window_ms,
    )


# 创建math_agent_graph实例的函数
def get_math_agent_graph():
    """
    获取math_agent_graph实例
    每次调用都重新创建，确保使用最新的代码
    """
    return create_math_agent_graph()


@router.post("/{thread_id}/runs", response_model=Run)
async def create_run(thread_id: str, request: RunCreateRequest):
    """
    创建运行（非流式）
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")

    # 获取线程关联的用户ID（如果有）
    thread = threads[thread_id]
    user_id = thread.get("user_id")

    run_id = generate_id()
    now = get_current_timestamp()

    run = {
        "run_id": run_id,
        "thread_id": thread_id,
        "user_id": user_id,
        "assistant_id": request.assistant_id,
        "created_at": now,
        "updated_at": now,
        "status": "pending",
        "input": request.input,
        "output": None,
        "error": None,
        "metadata": request.metadata or {},
    }

    runs[run_id] = run

    try:
        # 转换输入格式
        graph_input = _convert_input_format(request.input)

        # 调用 LangGraph
        math_agent_graph = get_math_agent_graph()
        result = await math_agent_graph.ainvoke(graph_input)

        run["status"] = "success"
        run["output"] = result
        run["updated_at"] = get_current_timestamp()

        # 更新线程状态
        threads[thread_id]["state"] = result
        threads[thread_id]["updated_at"] = get_current_timestamp()

        logger.info(f"Completed run {run_id} for thread {thread_id}")

    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)
        run["updated_at"] = get_current_timestamp()
        logger.error(f"Error in run {run_id}: {str(e)}")

    return Run(**run)


@router.get("/users/{user_id}/runs", response_model=list[RunWithUser])
async def get_user_runs(
    user_id: str,
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    status: Optional[str] = Query(None, description="状态过滤"),
):
    """
    获取用户的所有运行记录
    """
    # 验证用户是否存在
    user = user_system.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 过滤用户的运行记录
    user_runs = [r for r in runs.values() if r.get("user_id") == user_id]

    # 状态过滤
    if status:
        user_runs = [r for r in user_runs if r.get("status") == status]

    # 按更新时间倒序排列
    user_runs.sort(key=lambda x: x["updated_at"], reverse=True)

    # 分页
    user_runs = user_runs[offset : offset + limit]

    return [RunWithUser(**r) for r in user_runs]


@router.post("/{thread_id}/runs/stream")
async def create_run_stream(thread_id: str, request: RunCreateRequest):
    """
    创建运行（流式）
    LangGraph API 标准端点
    """
    logger.info(
        f"收到流式请求: thread_id={thread_id}, assistant_id={request.assistant_id}"
    )
    logger.info(f"请求输入摘要: {_summarize_input_payload(request.input)}")

    # 如果线程不存在，自动创建
    if thread_id not in threads:
        now = get_current_timestamp()
        threads[thread_id] = {
            "thread_id": thread_id,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata or {},
            "state": {"messages": []},  # 确保state.messages被正确初始化
            "messages": [],
        }
        logger.info(f"自动创建线程: {thread_id}")

    # 获取线程关联的用户ID（如果有）
    thread = threads[thread_id]
    user_id = thread.get("user_id")

    run_id = generate_id()
    now = get_current_timestamp()

    run = {
        "run_id": run_id,
        "thread_id": thread_id,
        "user_id": user_id,
        "assistant_id": request.assistant_id,
        "created_at": now,
        "updated_at": now,
        "status": "running",
        "input": request.input,
        "output": None,
        "error": None,
        "metadata": request.metadata or {},
    }

    runs[run_id] = run

    async def event_generator():
        """生成 SSE 事件流"""
        try:
            start_time = time.perf_counter()
            first_update_ms = None
            first_message_ms = None
            final_message_ms = None
            node_finish_times: Dict[str, int] = {}
            node_update_counts: Dict[str, int] = {}

            logger.info(f"========== 开始处理请求 ==========")
            logger.info(f"线程 ID: {thread_id}")
            logger.info(f"运行 ID: {run_id}")
            logger.info(f"助手 ID: {request.assistant_id}")
            logger.info(f"输入摘要: {_summarize_input_payload(request.input)}")

            # 发送开始事件
            yield f"event: metadata\ndata: {json.dumps({'run_id': run_id, 'status': 'started'})}\n\n"

            # 转换输入格式
            graph_input = _convert_input_format(request.input)

            current_state = threads[thread_id].get("state") or {}
            current_messages = current_state.get("messages", []) or threads[thread_id].get("messages", [])

            # 继承线程中的持久状态，避免多轮对话时丢失上下文。
            for carry_key in ("chat_history", "lesson_plan_session_id", "context"):
                if carry_key not in graph_input and carry_key in current_state:
                    graph_input[carry_key] = current_state.get(carry_key)

            # 优先使用请求中的消息，但会和线程已有历史合并，避免前端只发最后一条时把旧历史冲掉
            if "messages" in request.input and request.input["messages"]:
                graph_input["messages"] = _merge_message_lists(
                    current_messages,
                    request.input["messages"],
                )
                logger.info(
                    "合并请求消息与线程历史，请求=%s 条，线程已有=%s 条，合并后=%s 条",
                    len(request.input["messages"]),
                    len(current_messages),
                    len(graph_input["messages"]),
                )
            else:
                graph_input["messages"] = current_messages
                logger.info(
                    f"使用线程state中的消息历史，共 {len(current_messages)} 条消息"
                )

            # 流式调用 LangGraph
            chunk_count = 0
            ai_message_id = None
            ai_message_content = ""
            latest_state = dict(current_state) if isinstance(current_state, dict) else {}
            for key, value in graph_input.items():
                if key == "messages":
                    latest_state["messages"] = _merge_message_lists(
                        latest_state.get("messages", []),
                        value,
                    )
                else:
                    latest_state[key] = value

            math_agent_graph = get_math_agent_graph()

            # 使用 updates 模式，手动累积完整状态后以 values 事件发给前端
            # 前端 useStream hook 期望 values 事件包含完整状态
            async for chunk in math_agent_graph.astream(
                graph_input, stream_mode="updates"
            ):
                chunk_count += 1

                for node_name, node_output in chunk.items():
                    if node_output is None:
                        node_output = {}

                    # 累积状态：messages 字段需要合并而非替换
                    if isinstance(node_output, dict):
                        for key, value in node_output.items():
                            if key == "messages" and isinstance(value, list):
                                latest_state["messages"] = _merge_message_lists(
                                    latest_state.get("messages", []),
                                    value,
                                )
                            else:
                                latest_state[key] = value

                    elapsed_ms = _elapsed_ms(start_time)
                    node_finish_times[node_name] = elapsed_ms
                    node_update_counts[node_name] = (
                        node_update_counts.get(node_name, 0) + 1
                    )
                    if first_update_ms is None:
                        first_update_ms = elapsed_ms

                    threads[thread_id]["state"] = latest_state
                    threads[thread_id]["updated_at"] = get_current_timestamp()
                    threads[thread_id]["messages"] = latest_state.get("messages", [])

                    if RUN_STREAM_LOG_MODE in {"verbose", "summary"}:
                        msg_count = len(latest_state.get("messages", []))
                        logger.info(
                            f"  📌 节点: {node_name}, messages={msg_count}, since_start_ms={elapsed_ms}"
                        )

                    # 发送完整累积状态作为 values 事件
                    try:
                        yield f"event: values\ndata: {json.dumps(latest_state, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
                    except Exception as e:
                        logger.error(f"JSON序列化 values 失败: {e}")
                        # 回退：至少发送 messages 不丢
                        try:
                            fallback = {"messages": latest_state.get("messages", [])}
                            yield f"event: values\ndata: {json.dumps(fallback, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
                        except Exception:
                            pass

            # 更新线程状态
            threads[thread_id]["state"] = latest_state
            threads[thread_id]["updated_at"] = get_current_timestamp()
            if isinstance(latest_state, dict) and "messages" in latest_state:
                threads[thread_id]["messages"] = latest_state["messages"]

            # 更新运行状态
            runs[run_id]["status"] = "success"
            runs[run_id]["updated_at"] = get_current_timestamp()

            total_ms = _elapsed_ms(start_time)
            _log_stream_timing_summary(
                total_ms=total_ms,
                first_update_ms=first_update_ms,
                first_message_ms=first_message_ms,
                final_message_ms=final_message_ms,
                chunk_count=chunk_count,
                node_finish_times=node_finish_times,
                node_update_counts=node_update_counts,
            )
            logger.info(f"✅ 流式处理完成")

        except Exception as e:
            logger.error(f"❌ 流式处理失败: {str(e)}")
            runs[run_id]["status"] = "error"
            runs[run_id]["error"] = str(e)
            runs[run_id]["updated_at"] = get_current_timestamp()

            # 发送错误事件
            yield f"event: error\ndata: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _convert_input_format(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    转换输入格式：将 messages 转换为 user_input

    Args:
        input_data: 输入数据

    Returns:
        转换后的输入数据
    """
    graph_input = input_data.copy()

    if "messages" in graph_input:
        messages = graph_input["messages"]
        if messages and len(messages) > 0:
            last_message = messages[-1]
            if isinstance(last_message, dict):
                if "content" in last_message:
                    if isinstance(last_message["content"], str):
                        graph_input["user_input"] = last_message["content"]
                    elif (
                        isinstance(last_message["content"], list)
                        and len(last_message["content"]) > 0
                    ):
                        content_item = last_message["content"][0]
                        if isinstance(content_item, dict) and "text" in content_item:
                            graph_input["user_input"] = content_item["text"]

    # 从context中提取lesson_plan_session_id
    if "context" in graph_input and graph_input["context"]:
        context = graph_input["context"]
        if isinstance(context, dict) and "lesson_plan_session_id" in context:
            graph_input["lesson_plan_session_id"] = context["lesson_plan_session_id"]
            logger.info(
                f"💾 从context中提取教案会话ID: {context['lesson_plan_session_id']}"
            )

    # 确保user_input存在
    if "user_input" not in graph_input:
        graph_input["user_input"] = ""

    if RUN_STREAM_LOG_MODE in {"verbose", "summary"}:
        logger.info(f"🔄 转换输入格式摘要: {_summarize_input_payload(graph_input)}")

    return graph_input
