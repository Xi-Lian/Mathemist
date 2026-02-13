from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MathAgentState:
    """高中数学资源智能体状态定义"""
    
    # 对话消息（LangGraph SDK 期望的字段）
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # 用户输入
    user_input: str = ""
    
    # 意图理解
    intent: Optional[str] = None  # 可能的值: "search", "generate_lesson_plan", "visualization"
    intents: List[Dict[str, Any]] = field(default_factory=list)  # 多个意图及其置信度
    
    # 检索结果
    retrieved_resources: Optional[List[Dict[str, Any]]] = None
    
    # 教案生成
    lesson_plan: Optional[str] = None
    
    # 可视化设计建议
    visualization_suggestions: Optional[str] = None
    
    # 搜索结果
    search_results: Optional[str] = None
    
    # 最终响应
    response: Optional[str] = None
    
    # 对话历史
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    
    # 错误信息
    error: Optional[str] = None
    
    # 状态追踪
    current_step: Optional[str] = None
    
    # 上下文信息
    context: Optional[Dict[str, Any]] = None
