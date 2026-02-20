"""
线程相关路由模块

职责：
- 处理线程相关的API请求
- 提供线程创建、查询、搜索接口
- 支持线程与用户关联

依赖：
- fastapi
- app.api.models (数据模型)
- app.utils (工具函数)
- app.core.user_system (用户系统)
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body, Query
from app.api.models import Thread, ThreadCreateRequest, ThreadWithUser, ThreadCreateWithUserRequest
from app.utils import generate_id, get_current_timestamp
from app.core.user_system import user_system

router = APIRouter()

# 内存存储线程（生产环境应该使用数据库）
threads: Dict[str, Dict[str, Any]] = {}


@router.post("/threads", response_model=Thread)
async def create_thread(request: ThreadCreateRequest):
    """
    创建新线程（不关联用户，向后兼容）
    LangGraph API 标准端点
    """
    thread_id = generate_id()
    now = get_current_timestamp()
    
    thread = {
        "thread_id": thread_id,
        "created_at": now,
        "updated_at": now,
        "metadata": request.metadata or {},
        "state": None
    }
    
    threads[thread_id] = thread
    
    return Thread(**thread)


@router.post("/users/{user_id}/threads", response_model=ThreadWithUser)
async def create_thread_for_user(user_id: str, request: ThreadCreateWithUserRequest):
    """
    为用户创建新线程
    """
    # 验证用户是否存在
    user = user_system.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    thread_id = generate_id()
    now = get_current_timestamp()
    
    thread = {
        "thread_id": thread_id,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now,
        "metadata": request.metadata or {},
        "state": None
    }
    
    threads[thread_id] = thread
    
    return ThreadWithUser(**thread)


@router.get("/threads/{thread_id}", response_model=Thread)
async def get_thread(thread_id: str):
    """
    获取线程信息
    LangGraph API 标准端点
    
    如果线程不存在，自动创建一个新线程
    """
    if thread_id not in threads:
        print(f"⚠️  线程 {thread_id} 不存在，自动创建新线程")
        now = get_current_timestamp()
        thread = {
            "thread_id": thread_id,
            "created_at": now,
            "updated_at": now,
            "metadata": {},
            "state": None
        }
        threads[thread_id] = thread
    
    return Thread(**threads[thread_id])


@router.get("/users/{user_id}/threads", response_model=list[ThreadWithUser])
async def get_user_threads(
    user_id: str,
    limit: int = Query(100, ge=1, le=100, description="返回数量限制"),
    offset: int = Query(0, ge=0, description="偏移量")
):
    """
    获取用户的所有线程
    """
    # 验证用户是否存在
    user = user_system.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 过滤用户的线程
    user_threads = [
        t for t in threads.values()
        if t.get("user_id") == user_id
    ]
    
    # 按更新时间倒序排列
    user_threads.sort(
        key=lambda x: x["updated_at"],
        reverse=True
    )
    
    # 分页
    user_threads = user_threads[offset:offset + limit]
    
    return [ThreadWithUser(**t) for t in user_threads]


@router.post("/threads/search")
async def search_threads(query: Dict[str, Any] = Body(default={})):
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
    user_id = query.get("user_id")
    
    # 应用过滤条件
    if ids:
        thread_list = [t for t in thread_list if t["thread_id"] in ids]
    
    if user_id:
        thread_list = [t for t in thread_list if t.get("user_id") == user_id]
    
    if status:
        thread_list = [t for t in thread_list if t.get("status") == status]
    
    if metadata:
        thread_list = [t for t in thread_list if all(
            t.get("metadata", {}).get(k) == v 
            for k, v in metadata.items()
        )]
    
    # 应用分页
    total = len(thread_list)
    thread_list = thread_list[offset:offset+limit]
    
    return {
        "threads": thread_list,
        "total": total
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


@router.post("/threads/{thread_id}/history")
async def get_thread_history(thread_id: str):
    """
    获取线程历史消息
    LangGraph API 标准端点
    
    注意：LangGraph SDK 期望直接返回消息数组，而不是包含 messages 字段的对象
    
    如果线程不存在，自动创建一个新线程并返回空消息列表
    """
    if thread_id not in threads:
        print(f"⚠️  线程 {thread_id} 不存在，自动创建新线程")
        now = get_current_timestamp()
        thread = {
            "thread_id": thread_id,
            "created_at": now,
            "updated_at": now,
            "metadata": {},
            "state": None,
            "messages": []
        }
        threads[thread_id] = thread
        return []
    
    # 返回线程的历史消息（如果有）
    thread = threads[thread_id]
    messages = thread.get("messages", [])
    
    # 直接返回消息数组，符合 LangGraph SDK 的期望
    return messages
