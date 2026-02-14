"""
助手相关路由模块

职责：
- 处理助手相关的API请求
- 提供助手信息查询接口

依赖：
- fastapi
- app.api.models (数据模型)
- app.utils.constants (常量)
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from app.api.models import AssistantInfo, GraphInfo, SchemaInfo
from app.utils.constants import (
    ASSISTANT_ID,
    ASSISTANT_NAME,
    ASSISTANT_DESCRIPTION,
    GRAPH_ID,
    MODEL_NAME,
    VERSION,
    CATEGORY
)

router = APIRouter()


@router.get("/assistants/{assistant_id}", response_model=AssistantInfo)
async def get_assistant(assistant_id: str):
    """
    获取助手信息
    LangGraph API 标准端点
    """
    if assistant_id != ASSISTANT_ID:
        raise HTTPException(
            status_code=404, 
            detail=f"Assistant {assistant_id} not found"
        )
    
    return AssistantInfo(
        assistant_id=ASSISTANT_ID,
        name=ASSISTANT_NAME,
        description=ASSISTANT_DESCRIPTION,
        config={
            "graph": GRAPH_ID,
            "model": MODEL_NAME
        }
    )


@router.get("/assistants/{assistant_id}/graph", response_model=GraphInfo)
async def get_assistant_graph(assistant_id: str, xray: int = None):
    """
    获取助手的图结构
    LangGraph API 标准端点
    """
    if assistant_id != ASSISTANT_ID:
        raise HTTPException(
            status_code=404, 
            detail=f"Assistant {assistant_id} not found"
        )
    
    return GraphInfo(
        nodes=[
            {"id": "intent_understanding", "name": "意图理解"},
            {"id": "resource_retrieval", "name": "资源检索"},
            {"id": "lesson_plan_generation", "name": "教案生成"},
            {"id": "visualization_suggestions", "name": "可视化建议"},
            {"id": "response_formatting", "name": "响应生成"}
        ],
        edges=[
            {"source": "intent_understanding", "target": "resource_retrieval"},
            {"source": "resource_retrieval", "target": "lesson_plan_generation"},
            {"source": "lesson_plan_generation", "target": "visualization_suggestions"},
            {"source": "visualization_suggestions", "target": "response_formatting"}
        ]
    )


@router.get("/assistants/{assistant_id}/schemas", response_model=SchemaInfo)
async def get_assistant_schemas(assistant_id: str):
    """
    获取助手的图模式
    LangGraph API 标准端点
    """
    if assistant_id != ASSISTANT_ID:
        raise HTTPException(
            status_code=404, 
            detail=f"Assistant {assistant_id} not found"
        )
    
    return SchemaInfo(
        state_schema={
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
        input_schema={
            "type": "object",
            "properties": {
                "user_input": {"type": "string"}
            }
        },
        output_schema={
            "type": "object",
            "properties": {
                "response": {"type": "string"}
            }
        }
    )


@router.post("/assistants/search")
async def search_assistants(query: Dict[str, Any] = None):
    """
    搜索助手
    LangGraph API 标准端点
    """
    if query is None:
        query = {}
    
    graph_id = query.get("graph_id")
    metadata = query.get("metadata")
    limit = query.get("limit", 10)
    offset = query.get("offset", 0)
    
    assistants = [
        {
            "assistant_id": ASSISTANT_ID,
            "name": ASSISTANT_NAME,
            "description": "智能检索和生成高中数学教学资源的AI助手",
            "graph_id": GRAPH_ID,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "metadata": {
                "version": VERSION,
                "category": CATEGORY
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
                "assistant_id": ASSISTANT_ID,
                "name": ASSISTANT_NAME,
                "description": ASSISTANT_DESCRIPTION,
                "config": {
                    "graph": GRAPH_ID,
                    "model": MODEL_NAME
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
                "graph_id": GRAPH_ID,
                "name": ASSISTANT_NAME,
                "description": ASSISTANT_DESCRIPTION
            }
        ],
        "assistants": [
            {
                "assistant_id": ASSISTANT_ID,
                "name": ASSISTANT_NAME,
                "description": ASSISTANT_DESCRIPTION,
                "config": {
                    "graph": GRAPH_ID,
                    "model": MODEL_NAME
                }
            }
        ]
    }
