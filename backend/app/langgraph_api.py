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
from app.api.routes import assistants, threads, runs, users

logger = logging.getLogger(__name__)

# 创建主路由器
router = APIRouter(prefix="", tags=["LangGraph API"])

# 注册子路由
router.include_router(assistants.router)
router.include_router(threads.router)
router.include_router(runs.router)
router.include_router(users.router)

# 导出路由器供main.py使用
__all__ = ["router"]
