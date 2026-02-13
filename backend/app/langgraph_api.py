import os
import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator
from datetime import datetime
from fastapi import APIRouter, HTTPException, Request, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.graph import create_math_agent_graph

# 创建math_agent_graph实例
math_agent_graph = create_math_agent_graph()
from app.state import MathAgentState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["LangGraph API"])

# 内存存储线程和运行状态（生产环境应该使用数据库）
threads: Dict[str, Dict[str, Any]] = {}
runs: Dict[str, Dict[str, Any]] = {}

# 辅助函数
def generate_id() -> str:
    """生成唯一ID"""
    import uuid
    return str(uuid.uuid4())

class CustomJSONEncoder(json.JSONEncoder):
    """自定义 JSON 编码器，处理不可序列化的对象"""
    def default(self, obj):
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)

class ThreadCreateRequest(BaseModel):
    """创建线程请求"""
    metadata: Optional[Dict[str, Any]] = None

class Thread(BaseModel):
    """线程模型"""
    thread_id: str
    created_at: str
    updated_at: str
    metadata: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None

class RunCreateRequest(BaseModel):
    """创建运行请求"""
    assistant_id: str
    input: Dict[str, Any]
    config: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class Run(BaseModel):
    """运行模型"""
    run_id: str
    thread_id: str
    assistant_id: str
    created_at: str
    updated_at: str
    status: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@router.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """
    获取助手信息
    LangGraph API 标准端点
    """
    if assistant_id != "math-agent":
        raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
    
    return {
        "assistant_id": "math-agent",
        "name": "高中数学资源智能体",
        "description": "提供高中数学教案生成、资源检索、可视化设计建议等功能",
        "config": {
            "graph": "math_agent_graph",
            "model": "deepseek"
        }
    }

@router.get("/assistants/{assistant_id}/graph")
async def get_assistant_graph(assistant_id: str, xray: Optional[int] = None):
    """
    获取助手的图结构
    LangGraph API 标准端点
    """
    if assistant_id != "math-agent":
        raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
    
    return {
        "nodes": [
            {"id": "intent_understanding", "name": "意图理解"},
            {"id": "resource_retrieval", "name": "资源检索"},
            {"id": "lesson_plan_generation", "name": "教案生成"},
            {"id": "visualization_suggestions", "name": "可视化建议"},
            {"id": "response_generation", "name": "响应生成"}
        ],
        "edges": [
            {"source": "intent_understanding", "target": "resource_retrieval"},
            {"source": "resource_retrieval", "target": "lesson_plan_generation"},
            {"source": "lesson_plan_generation", "target": "visualization_suggestions"},
            {"source": "visualization_suggestions", "target": "response_generation"}
        ]
    }

@router.get("/assistants/{assistant_id}/schemas")
async def get_assistant_schemas(assistant_id: str):
    """
    获取助手的图模式
    LangGraph API 标准端点
    """
    if assistant_id != "math-agent":
        raise HTTPException(status_code=404, detail=f"Assistant {assistant_id} not found")
    
    return {
        "state_schema": {
            "type": "object",
            "properties": {
                "user_input": {"type": "string"},
                "intent": {"type": "string"},
                "lesson_plan": {"type": "object"},
                "visualization_suggestions": {"type": "array"},
                "retrieved_resources": {"type": "object"},
                "chat_history": {"type": "array"}
            }
        },
        "input_schema": {
            "type": "object",
            "properties": {
                "user_input": {"type": "string"}
            }
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "response": {"type": "string"}
            }
        }
    }

@router.post("/assistants/search")
async def search_assistants(
    query: Dict[str, Any] = Body(default={})
):
    """
    搜索助手
    LangGraph API 标准端点
    """
    graph_id = query.get("graph_id")
    metadata = query.get("metadata")
    limit = query.get("limit", 10)
    offset = query.get("offset", 0)
    
    assistants = [
        {
            "assistant_id": "math-agent",
            "name": "高中数学资源智能体",
            "description": "智能检索和生成高中数学教学资源的AI助手",
            "graph_id": "math-agent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "metadata": {
                "version": "1.0.0",
                "category": "education"
            }
        }
    ]
    
    # 应用过滤条件
    if graph_id:
        assistants = [a for a in assistants if a.get("graph_id") == graph_id]
    
    if metadata:
        assistants = [a for a in assistants if all(
            a.get("metadata", {}).get(k) == v 
            for k, v in metadata.items()
        )]
    
    # 应用分页
    total = len(assistants)
    assistants = assistants[offset:offset+limit]
    
    return {
        "assistants": assistants,
        "total": total
    }

@router.get("/assistants")
async def list_assistants():
    """
    列出所有助手
    LangGraph API 标准端点
    """
    return {
        "assistants": [
            {
                "assistant_id": "math-agent",
                "name": "高中数学资源智能体",
                "description": "提供高中数学教案生成、资源检索、可视化设计建议等功能",
                "config": {
                    "graph": "math_agent_graph",
                    "model": "deepseek"
                }
            }
        ]
    }

@router.get("/info")
async def get_info():
    """
    获取助手信息
    LangGraph API 标准端点
    """
    return {
        "graphs": [
            {
                "graph_id": "math-agent",
                "name": "高中数学资源智能体",
                "description": "提供高中数学教案生成、资源检索、可视化设计建议等功能"
            }
        ],
        "assistants": [
            {
                "assistant_id": "math-agent",
                "name": "高中数学资源智能体",
                "description": "提供高中数学教案生成、资源检索、可视化设计建议等功能",
                "config": {
                    "graph": "math_agent_graph",
                    "model": "deepseek"
                }
            }
        ]
    }

@router.post("/threads", response_model=Thread)
async def create_thread(request: ThreadCreateRequest):
    """
    创建新线程
    LangGraph API 标准端点
    """
    thread_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    thread = {
        "thread_id": thread_id,
        "created_at": now,
        "updated_at": now,
        "metadata": request.metadata or {},
        "state": None
    }
    
    threads[thread_id] = thread
    logger.info(f"Created thread: {thread_id}")
    
    return Thread(**thread)

@router.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """
    获取线程信息
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    return Thread(**threads[thread_id])

@router.post("/threads/search")
async def search_threads(
    query: Dict[str, Any] = Body(default={})
):
    """
    搜索线程
    LangGraph API 标准端点
    """
    thread_list = list(threads.values())
    
    metadata = query.get("metadata")
    ids = query.get("ids")
    limit = query.get("limit", 10)
    offset = query.get("offset", 0)
    status = query.get("status")
    sort_by = query.get("sort_by")
    sort_order = query.get("sort_order")
    select = query.get("select")
    
    # 应用过滤条件
    if ids:
        thread_list = [t for t in thread_list if t["thread_id"] in ids]
    
    if status:
        thread_list = [t for t in thread_list if t.get("status") == status]
    
    if metadata:
        thread_list = [t for t in thread_list if all(
            t.get("metadata", {}).get(k) == v 
            for k, v in metadata.items()
        )]
    
    # 应用排序
    if sort_by:
        reverse = sort_order == "desc"
        if sort_by == "created_at" or sort_by == "updated_at":
            thread_list.sort(key=lambda x: x.get(sort_by, ""), reverse=reverse)
    
    # 应用分页
    total = len(thread_list)
    thread_list = thread_list[offset:offset+limit]
    
    return {
        "threads": thread_list,
        "total": total
    }

@router.post("/threads/count")
async def count_threads(
    query: Dict[str, Any] = Body(default={})
):
    """
    统计线程数量
    LangGraph API 标准端点
    """
    thread_list = list(threads.values())
    
    metadata = query.get("metadata")
    values = query.get("values")
    status = query.get("status")
    
    # 应用过滤条件
    if status:
        thread_list = [t for t in thread_list if t.get("status") == status]
    
    if metadata:
        thread_list = [t for t in thread_list if all(
            t.get("metadata", {}).get(k) == v 
            for k, v in metadata.items()
        )]
    
    return {
        "count": len(thread_list)
    }

@router.get("/threads")
async def list_threads(limit: int = 100, offset: int = 0):
    """
    列出所有线程
    LangGraph API 标准端点
    """
    thread_list = list(threads.values())
    return {
        "threads": thread_list[offset:offset+limit],
        "total": len(thread_list)
    }

@router.post("/threads/{thread_id}/runs", response_model=Run)
async def create_run(thread_id: str, request: RunCreateRequest):
    """
    创建运行（非流式）
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    run_id = generate_id()
    now = datetime.utcnow().isoformat()
    
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
        # 转换输入格式：将 messages 转换为 user_input
        graph_input = request.input.copy()
        if "messages" in graph_input:
            # 如果有 messages 字段，提取最后一条消息的内容作为 user_input
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
        
        # 调用 LangGraph
        result = await math_agent_graph.ainvoke(graph_input)
        
        run["status"] = "success"
        run["output"] = result
        run["updated_at"] = datetime.utcnow().isoformat()
        
        # 更新线程状态
        threads[thread_id]["state"] = result
        threads[thread_id]["updated_at"] = datetime.utcnow().isoformat()
        
        logger.info(f"Completed run {run_id} for thread {thread_id}")
        
    except Exception as e:
        run["status"] = "error"
        run["error"] = str(e)
        run["updated_at"] = datetime.utcnow().isoformat()
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
        now = datetime.utcnow().isoformat()
        threads[thread_id] = {
            "thread_id": thread_id,
            "created_at": now,
            "updated_at": now,
            "metadata": request.metadata or {},
            "state": {}
        }
        logger.info(f"自动创建线程: {thread_id}")
    
    run_id = generate_id()
    now = datetime.utcnow().isoformat()
    
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
            logger.info("📤 发送开始事件")
            
            # 转换输入格式：将 messages 转换为 user_input
            graph_input = request.input.copy() if request.input else {}
            logger.info(f"📋 graph_input 类型: {type(graph_input)}")
            logger.info(f"📋 graph_input 内容: {graph_input}")
            
            user_message = None
            if "messages" in graph_input:
                # 如果有 messages 字段，提取最后一条消息的内容作为 user_input
                messages = graph_input["messages"]
                logger.info(f"📨 messages 类型: {type(messages)}")
                logger.info(f"📨 messages 长度: {len(messages) if messages else 0}")
                
                if messages and len(messages) > 0:
                    last_message = messages[-1]
                    logger.info(f"💬 last_message 类型: {type(last_message)}")
                    logger.info(f"💬 last_message 内容: {last_message}")
                    
                    if isinstance(last_message, dict):
                        user_message = last_message
                        logger.info(f"✅ user_message 已设置")
                        
                        if "content" in last_message:
                            logger.info(f"📄 content 类型: {type(last_message['content'])}")
                            
                            if isinstance(last_message["content"], str):
                                graph_input["user_input"] = last_message["content"]
                                logger.info(f"✅ user_input (字符串): {graph_input['user_input']}")
                            elif isinstance(last_message["content"], list) and len(last_message["content"]) > 0:
                                content_item = last_message["content"][0]
                                logger.info(f"📦 content_item 类型: {type(content_item)}")
                                logger.info(f"📦 content_item 内容: {content_item}")
                                
                                if content_item and isinstance(content_item, dict) and "text" in content_item:
                                    graph_input["user_input"] = content_item["text"]
                                    logger.info(f"✅ user_input (列表): {graph_input['user_input']}")
            
            logger.info(f"📝 用户输入: {graph_input.get('user_input', 'N/A')}")
            
            # 初始化 messages 数组
            logger.info(f"🔍 获取线程状态...")
            logger.info(f"🔍 threads 类型: {type(threads)}")
            logger.info(f"🔍 thread_id: {thread_id}")
            logger.info(f"🔍 thread_id 是否在 threads 中: {thread_id in threads}")
            
            if thread_id not in threads:
                logger.error(f"❌ 线程 {thread_id} 不存在于 threads 中")
                raise ValueError(f"线程 {thread_id} 不存在")
            
            thread = threads[thread_id]
            logger.info(f"🔍 thread 类型: {type(thread)}")
            logger.info(f"🔍 thread 内容: {thread}")
            
            current_state = thread.get("state") or {}
            logger.info(f"🔍 current_state 类型: {type(current_state)}")
            logger.info(f"🔍 current_state 内容: {current_state}")
            
            current_messages = current_state.get("messages", [])
            logger.info(f"🔍 current_messages 类型: {type(current_messages)}")
            logger.info(f"🔍 current_messages 长度: {len(current_messages)}")
            
            # 添加用户消息
            if user_message:
                current_messages.append(user_message)
                graph_input["messages"] = current_messages
            
            # 流式调用 LangGraph
            logger.info("🔄 开始流式调用 LangGraph")
            chunk_count = 0
            ai_message_id = None
            ai_message_content = ""
            
            async for chunk in math_agent_graph.astream(
                graph_input,
                stream_mode="updates"
            ):
                chunk_count += 1
                logger.info(f"📦 收到第 {chunk_count} 个 chunk: {list(chunk.keys())}")
                # 将 chunk 转换为 LangGraph SDK 期望的格式
                for node_name, node_output in chunk.items():
                    # 确保 node_output 不是 None
                    if node_output is None:
                        node_output = {}
                    
                    logger.info(f"  📌 节点: {node_name}")
                    logger.info(f"  📄 输出: {node_output}")
                    # 发送 values 事件（用于状态更新）
                    try:
                        yield f"event: values\ndata: {json.dumps(node_output, ensure_ascii=False, cls=CustomJSONEncoder)}\n\n"
                    except Exception as e:
                        logger.error(f"JSON序列化失败: {e}, node_output: {type(node_output)}")
                        yield f"event: values\ndata: {json.dumps({}, ensure_ascii=False)}\n\n"
                    
                    # 如果节点输出包含 response，发送 messages 事件
                    if isinstance(node_output, dict) and "response" in node_output:
                        response_text = node_output["response"]
                        
                        # 创建或更新 AI 消息
                        if ai_message_id is None:
                            ai_message_id = generate_id()
                        
                        ai_message_content = response_text
                        
                        # 创建消息对象（LangGraph SDK 期望的格式）
                        message = {
                            "type": "ai",
                            "content": ai_message_content,
                            "id": ai_message_id
                        }
                        
                        # 更新 messages 数组
                        updated_messages = current_messages + [message]
                        
                        # 发送 messages 事件
                        yield f"event: messages\ndata: {json.dumps([message, {}], ensure_ascii=False)}\n\n"
                        logger.info(f"  💬 发送消息事件: {response_text[:100]}...")
                        
                        # 更新 graph_input 中的 messages
                        graph_input["messages"] = updated_messages
            
            logger.info(f"✅ 流式调用完成，共收到 {chunk_count} 个 chunk")
            
            # 获取最终状态
            logger.info("🔄 获取最终状态")
            final_result = await math_agent_graph.ainvoke(graph_input)
            logger.info(f"📊 最终状态: {final_result}")
            
            # 确保最终状态包含 messages
            if "messages" not in final_result:
                final_result["messages"] = graph_input.get("messages", [])
            
            # 发送完成事件
            run["status"] = "success"
            run["updated_at"] = datetime.utcnow().isoformat()
            run["output"] = final_result
            
            # 更新线程状态
            threads[thread_id]["state"] = final_result
            threads[thread_id]["updated_at"] = datetime.utcnow().isoformat()
            
            yield f"event: metadata\ndata: {json.dumps({'run_id': run_id, 'status': 'completed'})}\n\n"
            logger.info(f"Completed stream run {run_id} for thread {thread_id}")
            
        except Exception as e:
            run["status"] = "error"
            run["error"] = str(e)
            run["updated_at"] = datetime.utcnow().isoformat()
            logger.error(f"Error in stream run {run_id}: {str(e)}")
            
            error_data = {
                "event": "error",
                "data": {"error": str(e)}
            }
            yield f"event: error\ndata: {json.dumps(error_data, ensure_ascii=False)}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/threads/{thread_id}/runs/{run_id}", response_model=Run)
async def get_run(thread_id: str, run_id: str):
    """
    获取运行信息
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    if run_id not in runs:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    
    return Run(**runs[run_id])

@router.get("/threads/{thread_id}/state")
async def get_thread_state(thread_id: str, subgraphs: Optional[bool] = False):
    """
    获取线程状态
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    thread = threads[thread_id]
    return {
        "values": thread.get("state", {}),
        "next": [],
        "checkpoint": {
            "id": thread_id,
            "thread_id": thread_id,
            "timestamp": thread.get("updated_at", thread.get("created_at"))
        }
    }

@router.post("/threads/{thread_id}/state")
async def update_thread_state(thread_id: str, values: Dict[str, Any]):
    """
    更新线程状态
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    threads[thread_id]["state"] = values
    threads[thread_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return {
        "values": values,
        "checkpoint": {
            "id": thread_id,
            "thread_id": thread_id,
            "timestamp": threads[thread_id]["updated_at"]
        }
    }

@router.post("/threads/{thread_id}/state/checkpoint")
async def get_thread_state_checkpoint(thread_id: str, request: Dict[str, Any] = Body(default={})):
    """
    获取线程状态的检查点
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    thread = threads[thread_id]
    
    return {
        "values": thread.get("state", {}),
        "next": [],
        "checkpoint": {
            "id": thread_id,
            "thread_id": thread_id,
            "timestamp": thread.get("updated_at", thread.get("created_at"))
        }
    }

@router.get("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str, limit: int = 10, before: Optional[str] = None):
    """
    获取线程历史
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    thread = threads[thread_id]
    
    history = []
    if thread.get("state"):
        history.append({
            "values": thread["state"],
            "next": [],
            "checkpoint": {
                "id": thread_id,
                "thread_id": thread_id,
                "timestamp": thread.get("updated_at", thread.get("created_at"))
            },
            "parent_config": None,
            "metadata": thread.get("metadata", {})
        })
    
    return history[:limit]

@router.post("/threads/{thread_id}/history")
async def post_thread_history(thread_id: str, request: Dict[str, Any] = Body(default={})):
    """
    获取线程历史（POST 方法）
    LangGraph API 标准端点
    """
    limit = request.get("limit", 10)
    before = request.get("before")
    
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    thread = threads[thread_id]
    
    history = []
    if thread.get("state"):
        history.append({
            "values": thread["state"],
            "next": [],
            "checkpoint": {
                "id": thread_id,
                "thread_id": thread_id,
                "timestamp": thread.get("updated_at", thread.get("created_at"))
            },
            "parent_config": None,
            "metadata": thread.get("metadata", {})
        })
    
    return history[:limit]

@router.patch("/threads/{thread_id}")
async def update_thread(thread_id: str, metadata: Optional[Dict[str, Any]] = None, ttl: Optional[Dict[str, Any]] = None):
    """
    更新线程
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    if metadata is not None:
        threads[thread_id]["metadata"] = metadata
    
    threads[thread_id]["updated_at"] = datetime.utcnow().isoformat()
    
    return Thread(**threads[thread_id])

@router.get("/threads/{thread_id}/runs")
async def list_runs(thread_id: str, limit: int = 100, offset: int = 0):
    """
    列出线程的所有运行
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    thread_runs = [run for run in runs.values() if run["thread_id"] == thread_id]
    thread_runs.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "runs": thread_runs[offset:offset+limit],
        "total": len(thread_runs)
    }

@router.post("/threads/{thread_id}/copy")
async def copy_thread(thread_id: str):
    """
    复制线程
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    original_thread = threads[thread_id]
    new_thread_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    new_thread = {
        "thread_id": new_thread_id,
        "created_at": now,
        "updated_at": now,
        "metadata": original_thread.get("metadata", {}).copy(),
        "state": original_thread.get("state")
    }
    
    threads[new_thread_id] = new_thread
    logger.info(f"Copied thread {thread_id} to {new_thread_id}")
    
    return Thread(**new_thread)

@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """
    删除线程
    LangGraph API 标准端点
    """
    if thread_id not in threads:
        raise HTTPException(status_code=404, detail=f"Thread {thread_id} not found")
    
    # 删除线程及其所有运行
    del threads[thread_id]
    for run_id in list(runs.keys()):
        if runs[run_id]["thread_id"] == thread_id:
            del runs[run_id]
    
    logger.info(f"Deleted thread: {thread_id}")
    
    return {"status": "deleted", "thread_id": thread_id}
