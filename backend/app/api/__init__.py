"""
API模块

提供API相关的路由和数据模型：
- 助手相关路由
- 线程相关路由
- 运行相关路由
- 数据模型定义
"""

from .models import (
    AssistantInfo,
    GraphInfo,
    SchemaInfo,
    ThreadCreateRequest,
    Thread,
    RunCreateRequest,
    Run,
    Resource,
    RetrievedResources,
    IntentInfo,
    IntentAnalysisResult,
    LessonPlan,
    VisualizationSuggestion,
    AgentResponse,
    Message,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    SuccessResponse,
    PaginatedResponse
)

__all__ = [
    # 数据模型
    "AssistantInfo",
    "GraphInfo",
    "SchemaInfo",
    "ThreadCreateRequest",
    "Thread",
    "RunCreateRequest",
    "Run",
    "Resource",
    "RetrievedResources",
    "IntentInfo",
    "IntentAnalysisResult",
    "LessonPlan",
    "VisualizationSuggestion",
    "AgentResponse",
    "Message",
    "ChatRequest",
    "ChatResponse",
    "ErrorResponse",
    "SuccessResponse",
    "PaginatedResponse"
]
