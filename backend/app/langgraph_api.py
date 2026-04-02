"""
LangGraph API模块

职责：
- 提供LangGraph API接口
- 协调各个路由模块
- 处理流式和非流式请求

依赖：
- fastapi
- app.api.routes (路由模块)
- app.utils (工具函数)
"""

import logging
from fastapi import APIRouter
from app.api.routes import assistants, threads, runs, users, files
from app.utils.constants import (
    ASSISTANT_ID,
    ASSISTANT_NAME,
    ASSISTANT_DESCRIPTION,
    GRAPH_ID,
    MODEL_NAME
)

logger = logging.getLogger(__name__)

# 创建主路由器
router = APIRouter(prefix="/langgraph/math-agent", tags=["LangGraph API"])

# 注册子路由，为每个子路由器设置正确的前缀
router.include_router(assistants.router, prefix="/assistants")
router.include_router(threads.router, prefix="/threads")
router.include_router(runs.router, prefix="/threads")
router.include_router(users.router)
router.include_router(files.router, prefix="/files")


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

# 导出路由器供main.py使用
__all__ = ["router"]
