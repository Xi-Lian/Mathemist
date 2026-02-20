"""
API数据模型模块

职责：
- 定义API请求和响应的数据模型
- 提供数据验证
- 支持Pydantic模型

依赖：
- pydantic
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


class AssistantInfo(BaseModel):
    """助手信息模型"""
    assistant_id: str = Field(..., description="助手ID")
    name: str = Field(..., description="助手名称")
    description: str = Field(..., description="助手描述")
    config: Optional[Dict[str, Any]] = Field(default=None, description="配置信息")


class GraphInfo(BaseModel):
    """图结构信息模型"""
    nodes: List[Dict[str, str]] = Field(default_factory=list, description="节点列表")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="边列表")


class SchemaInfo(BaseModel):
    """模式信息模型"""
    state_schema: Dict[str, Any] = Field(default_factory=dict, description="状态模式")
    input_schema: Dict[str, Any] = Field(default_factory=dict, description="输入模式")
    output_schema: Dict[str, Any] = Field(default_factory=dict, description="输出模式")


class ThreadCreateRequest(BaseModel):
    """创建线程请求模型"""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class Thread(BaseModel):
    """线程模型"""
    thread_id: str = Field(..., description="线程ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    state: Optional[Dict[str, Any]] = Field(default=None, description="状态")


class RunCreateRequest(BaseModel):
    """创建运行请求模型"""
    assistant_id: str = Field(..., description="助手ID")
    input: Dict[str, Any] = Field(..., description="输入数据")
    config: Optional[Dict[str, Any]] = Field(default=None, description="配置")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class Run(BaseModel):
    """运行模型"""
    run_id: str = Field(..., description="运行ID")
    thread_id: str = Field(..., description="线程ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    assistant_id: str = Field(..., description="助手ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    status: str = Field(..., description="状态")
    input: Dict[str, Any] = Field(..., description="输入数据")
    output: Optional[Dict[str, Any]] = Field(default=None, description="输出数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class Resource(BaseModel):
    """资源模型"""
    title: str = Field(..., description="资源标题")
    content: str = Field(..., description="资源内容")
    source: str = Field(..., description="资源来源")
    relevance: float = Field(..., description="相关性分数")
    resource_type: Optional[str] = Field(default=None, description="资源类型")


class RetrievedResources(BaseModel):
    """检索到的资源模型"""
    theory_resources: List[Resource] = Field(default_factory=list, description="理论资源")
    lesson_plan_patterns: List[Resource] = Field(default_factory=list, description="教案资源")
    exercise_resources: List[Resource] = Field(default_factory=list, description="习题资源")
    visualization_examples: List[Resource] = Field(default_factory=list, description="可视化示例")
    general_resources: List[Resource] = Field(default_factory=list, description="通用资源")
    courseware_resources: List[Resource] = Field(default_factory=list, description="课件资源")
    lesson_case_resources: List[Resource] = Field(default_factory=list, description="课例资源")
    ggb_resources: List[Resource] = Field(default_factory=list, description="GGB资源")
    syllabus_resources: List[Resource] = Field(default_factory=list, description="教学大纲资源")


class IntentInfo(BaseModel):
    """意图信息模型"""
    type: str = Field(..., description="意图类型")
    confidence: float = Field(..., description="置信度")


class IntentAnalysisResult(BaseModel):
    """意图分析结果模型"""
    intent: str = Field(..., description="主要意图")
    intents: List[IntentInfo] = Field(default_factory=list, description="所有意图")
    current_step: str = Field(..., description="当前步骤")
    error: Optional[str] = Field(default=None, description="错误信息")


class LessonPlan(BaseModel):
    """教案模型"""
    content: str = Field(..., description="教案内容")
    theory_references: List[str] = Field(default_factory=list, description="理论引用")


class VisualizationSuggestion(BaseModel):
    """可视化建议模型"""
    content: str = Field(..., description="建议内容")
    examples: List[str] = Field(default_factory=list, description="参考示例")


class AgentResponse(BaseModel):
    """智能体响应模型"""
    response: str = Field(..., description="响应内容")
    intent: str = Field(..., description="意图类型")
    retrieved_resources: Optional[RetrievedResources] = Field(default=None, description="检索到的资源")
    lesson_plan: Optional[LessonPlan] = Field(default=None, description="生成的教案")
    visualization_suggestions: Optional[VisualizationSuggestion] = Field(default=None, description="可视化建议")
    current_step: str = Field(..., description="当前步骤")
    error: Optional[str] = Field(default=None, description="错误信息")


class Message(BaseModel):
    """消息模型"""
    role: str = Field(..., description="角色")
    content: str = Field(..., description="内容")
    id: Optional[str] = Field(default=None, description="消息ID")


class ChatRequest(BaseModel):
    """聊天请求模型"""
    messages: List[Message] = Field(..., description="消息列表")
    config: Optional[Dict[str, Any]] = Field(default=None, description="配置")


class ChatResponse(BaseModel):
    """聊天响应模型"""
    response: str = Field(..., description="响应内容")
    messages: List[Message] = Field(default_factory=list, description="消息列表")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="详细信息")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")


class SuccessResponse(BaseModel):
    """成功响应模型"""
    success: bool = Field(default=True, description="是否成功")
    message: Optional[str] = Field(default=None, description="消息")
    data: Optional[Dict[str, Any]] = Field(default=None, description="数据")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="时间戳")


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any] = Field(default_factory=list, description="项目列表")
    total: int = Field(..., description="总数")
    limit: int = Field(..., description="每页数量")
    offset: int = Field(..., description="偏移量")
    has_more: bool = Field(..., description="是否有更多")


class UserCreateRequest(BaseModel):
    """创建用户请求模型"""
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    preferences: Optional[Dict[str, Any]] = Field(default=None, description="偏好设置")


class UserLoginRequest(BaseModel):
    """用户登录请求模型"""
    email: str = Field(..., description="邮箱")


class UserResponse(BaseModel):
    """用户响应模型"""
    user_id: str = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    email: str = Field(..., description="邮箱")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="偏好设置")
    created_at: str = Field(..., description="创建时间")


class UserPreferencesUpdateRequest(BaseModel):
    """更新用户偏好请求模型"""
    preferences: Dict[str, Any] = Field(..., description="偏好设置")


class LessonPlanHistoryCreateRequest(BaseModel):
    """创建备课历史请求模型"""
    topic: str = Field(..., description="课题")
    chapter: Optional[str] = Field(default=None, description="章节")
    textbook: Optional[str] = Field(default=None, description="教材")
    teaching_goals: Optional[str] = Field(default=None, description="教学目标")
    teaching_framework: Optional[str] = Field(default=None, description="教学框架")
    lesson_plan_content: Optional[str] = Field(default=None, description="教案内容")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    notes: Optional[str] = Field(default=None, description="备注")


class LessonPlanHistoryUpdateRequest(BaseModel):
    """更新备课历史请求模型"""
    topic: Optional[str] = Field(default=None, description="课题")
    chapter: Optional[str] = Field(default=None, description="章节")
    textbook: Optional[str] = Field(default=None, description="教材")
    teaching_goals: Optional[str] = Field(default=None, description="教学目标")
    teaching_framework: Optional[str] = Field(default=None, description="教学框架")
    lesson_plan_content: Optional[str] = Field(default=None, description="教案内容")
    status: Optional[str] = Field(default=None, description="状态")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    notes: Optional[str] = Field(default=None, description="备注")


class LessonPlanHistoryResponse(BaseModel):
    """备课历史响应模型"""
    history_id: str = Field(..., description="历史记录ID")
    user_id: str = Field(..., description="用户ID")
    topic: str = Field(..., description="课题")
    chapter: Optional[str] = Field(default=None, description="章节")
    textbook: Optional[str] = Field(default=None, description="教材")
    teaching_goals: Optional[str] = Field(default=None, description="教学目标")
    teaching_framework: Optional[str] = Field(default=None, description="教学框架")
    lesson_plan_content: Optional[str] = Field(default=None, description="教案内容")
    status: str = Field(..., description="状态")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    notes: Optional[str] = Field(default=None, description="备注")


class ThreadCreateWithUserRequest(BaseModel):
    """创建线程请求模型（带用户）"""
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")


class ThreadWithUser(BaseModel):
    """线程模型（带用户）"""
    thread_id: str = Field(..., description="线程ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
    state: Optional[Dict[str, Any]] = Field(default=None, description="状态")


class RunWithUser(BaseModel):
    """运行模型（带用户）"""
    run_id: str = Field(..., description="运行ID")
    thread_id: str = Field(..., description="线程ID")
    user_id: Optional[str] = Field(default=None, description="用户ID")
    assistant_id: str = Field(..., description="助手ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    status: str = Field(..., description="状态")
    input: Dict[str, Any] = Field(..., description="输入数据")
    output: Optional[Dict[str, Any]] = Field(default=None, description="输出数据")
    error: Optional[str] = Field(default=None, description="错误信息")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="元数据")
