"""
运行相关路由模块

职责：
- 处理运行相关的API请求
- 提供运行创建、查询、流式接口

依赖：
- fastapi
- app.api.models (数据模型)
- app.utils (工具函数)
- app.graph (图实例)
- app.api.routes.threads (线程存储)
"""

import json
import logging
import uuid
from typing import Dict, Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import StreamingResponse
from app.api.models import Run, RunCreateRequest
from app.utils import generate_id, get_current_timestamp, CustomJSONEncoder
from app.graph import create_math_agent_graph
from app.api.routes import threads as threads_module

logger = logging.getLogger(__name__)

router = APIRouter()

# 内存存储运行（生产环境应该使用数据库）
runs: Dict[str, Dict[str, Any]] = {}
# 使用 threads 模块中的 threads 字典
threads = threads_module.threads

# 创建math_agent_graph实例的函数
def get_math_agent_graph():
    """
    获取math_agent_graph实例
    每次调用都重新创建，确保使用最新的代码
    """
    return create_math_agent_graph()


@router.post("/threads/{thread_id}/runs", response_model=Run)
async def create_run(thread_id: str, request: RunCreateRequest):
    """
    创建运行（非流式）
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(
            status_code=404, 
            detail=f"Thread {thread_id} not found"
        )
    
    run_id = generate_id()
    now = get_current_timestamp()
    
    run = {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": request.assistant_id,
        "created_at": now,
        "updated_at": now,
        "status": "pending",
        "input": request.input,
        "output": None,
        "error": None,
        "metadata": request.metadata or {}
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


@router.post("/threads/{thread_id}/runs/stream")
async def create_run_stream(thread_id: str, request: RunCreateRequest):
    """
    创建运行（流式）
    LangGraph API 标准端点
    """
    # 如果线程不存在，自动创建
    if thread_id not in threads:
        now = get_current_timestamp()
        threads[thread_id] = {
            "thread_id": thread_id,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata or {},
            "state": {},
            "messages": []
        }
        logger.info(f"自动创建线程: {thread_id}")
    
    run_id = generate_id()
    now = get_current_timestamp()
    
    run = {
        "run_id": run_id,
        "thread_id": thread_id,
        "assistant_id": request.assistant_id,
        "created_at": now,
        "updated_at": now,
        "status": "running",
        "input": request.input,
        "output": None,
        "error": None,
        "metadata": request.metadata or {}
    }
    
    runs[run_id] = run
    
    async def event_generator():
        """生成 SSE 事件流"""
        try:
            logger.info(f"========== 开始处理请求 ==========")
            logger.info(f"线程 ID: {thread_id}")
            logger.info(f"运行 ID: {run_id}")
            logger.info(f"助手 ID: {request.assistant_id}")
            logger.info(f"输入: {request.input}")
            
            # 发送开始事件
            yield f"event: metadata\ndata: {json.dumps({'run_id': run_id, 'status': 'started'})}\n\n"
            
            # 转换输入格式
            graph_input = _convert_input_format(request.input)
            
            # 初始化 messages 数组
            current_state = threads[thread_id].get("state") or {}
            current_messages = current_state.get("messages", [])
            
            # 添加用户消息
            user_message = None
            if "messages" in request.input:
                user_message = request.input["messages"][-1] if request.input["messages"] else None
                if user_message:
                    current_messages.append(user_message)
                    graph_input["messages"] = current_messages
            
            # 流式调用 LangGraph
            chunk_count = 0
            ai_message_id = None
            ai_message_content = ""
            
            math_agent_graph = get_math_agent_graph()
            
            async for chunk in math_agent_graph.astream(
                graph_input,
                stream_mode=["updates", "messages"]
            ):
                chunk_count += 1
                
                # 处理不同类型的 chunk
                # 当使用多个流模式时，chunk 的格式是 (event, data)
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    event, data = chunk
                    logger.info(f"📦 收到第 {chunk_count} 个 chunk: {event}")
                    
                    # 发送事件
                    if event == "updates":
                        # 发送 updates 事件
                        for node_name, node_output in data.items():
                            if node_output is None:
                                node_output = {}
                            
                            logger.info(f"  📌 节点: {node_name}")
                            logger.info(f"  📄 输出: {node_output}")
                            
                            # 发送 values 事件
                            try:
                                yield f"event: values\ndata: {json.dumps(node_output, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
                            except Exception as e:
                                logger.error(f"JSON序列化失败: {e}")
                                yield f"event: values\ndata: {json.dumps({}, ensure_ascii=False)}\n\n"
                            
                            # 不再从 updates 事件中发送 messages 事件，避免重复
                            # 只通过 messages 事件发送消息
                    
                    elif event == "messages":
                        # 发送 messages 事件
                        logger.info(f"  📌 messages: {data}")
                        
                        # 直接转发 messages 事件
                        if isinstance(data, list):
                            for message in data:
                                # 确保 message 包含必要的字段
                                if isinstance(message, dict):
                                    if "type" not in message:
                                        message["type"] = "ai"
                                    if "content" not in message:
                                        message["content"] = ""
                                    if "id" not in message:
                                        message["id"] = f"msg_{uuid.uuid4().hex}"
                                    # 将 AI 消息添加到线程的 messages 字段中
                                    if message["type"] == "ai":
                                        existing_messages = threads[thread_id].get("messages", [])
                                        # 检查是否已经存在相同 ID 的消息，避免重复
                                        message_exists = any(
                                            msg.get("id") == message.get("id") 
                                            for msg in existing_messages
                                        )
                                        if not message_exists:
                                            existing_messages.append(message)
                                            threads[thread_id]["messages"] = existing_messages
                                yield f"event: messages\ndata: {json.dumps([message, {}], ensure_ascii=False)}\n\n"
                    elif event == "messages-tuple":
                        # 发送 messages-tuple 事件
                        logger.info(f"  📌 messages-tuple: {data}")
                        
                        # 直接转发 messages-tuple 事件
                        if isinstance(data, list) and len(data) == 2:
                            message, metadata = data
                            # 确保 message 包含必要的字段
                            if isinstance(message, dict):
                                if "type" not in message:
                                    message["type"] = "ai"
                                if "content" not in message:
                                    message["content"] = ""
                                if "id" not in message:
                                    message["id"] = f"msg_{uuid.uuid4().hex}"
                                # 将 AI 消息添加到线程的 messages 字段中
                                if message["type"] == "ai":
                                    existing_messages = threads[thread_id].get("messages", [])
                                    # 检查是否已经存在相同 ID 的消息，避免重复
                                    message_exists = any(
                                        msg.get("id") == message.get("id") 
                                        for msg in existing_messages
                                    )
                                    if not message_exists:
                                        existing_messages.append(message)
                                        threads[thread_id]["messages"] = existing_messages
                            yield f"event: messages\ndata: {json.dumps([message, metadata], ensure_ascii=False)}\n\n"
                    else:
                        logger.info(f"  📌 其他事件: {event}")
                        # 直接转发其他事件
                        try:
                            yield f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
                        except Exception as e:
                            logger.error(f"JSON序列化失败: {e}")
                else:
                    # 兼容旧格式（单个流模式）
                    logger.info(f"📦 收到第 {chunk_count} 个 chunk: {list(chunk.keys())}")
                    
                    for node_name, node_output in chunk.items():
                        if node_output is None:
                            node_output = {}
                        
                        logger.info(f"  📌 节点: {node_name}")
                        logger.info(f"  📄 输出: {node_output}")
                        
                        # 发送 values 事件
                        try:
                            yield f"event: values\ndata: {json.dumps(node_output, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
                        except Exception as e:
                            logger.error(f"JSON序列化失败: {e}")
                            yield f"event: values\ndata: {json.dumps({}, ensure_ascii=False)}\n\n"
            
            # LangGraph 会自动处理 messages-tuple 事件，我们不需要手动发送
            
            # 更新线程状态和消息
            threads[thread_id]["state"] = graph_input
            threads[thread_id]["updated_at"] = get_current_timestamp()
            
            # AI 消息已经在发送 messages 事件时添加到线程的 messages 字段中了
            # 这里不需要再添加
            
            # 更新运行状态
            runs[run_id]["status"] = "success"
            runs[run_id]["updated_at"] = get_current_timestamp()
            
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
            "X-Accel-Buffering": "no"
        }
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
                    elif isinstance(last_message["content"], list) and len(last_message["content"]) > 0:
                        content_item = last_message["content"][0]
                        if isinstance(content_item, dict) and "text" in content_item:
                            graph_input["user_input"] = content_item["text"]
    
    return graph_input
