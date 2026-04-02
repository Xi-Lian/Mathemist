from typing import List, Dict, Any, Optional, Annotated
from dataclasses import dataclass, field
from langgraph.graph import add_messages


def merge_messages(left: List, right: List) -> List:
    """
    自定义 messages 合并函数：
    - 保留左侧（现有）消息
    - 添加右侧（新）消息
    - 根据 id 去重
    """
    if not left:
        return right or []
    if not right:
        return left

    # 创建 id -> message 的映射
    existing_ids = {msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None) for msg in left}

    result = list(left)
    for msg in right:
        msg_id = msg.get("id") if isinstance(msg, dict) else getattr(msg, "id", None)
        if msg_id and msg_id not in existing_ids:
            result.append(msg)
            existing_ids.add(msg_id)

    return result


@dataclass
class MathAgentState:
    """高中数学资源智能体状态定义"""

    messages: Annotated[List[Dict[str, Any]], merge_messages] = field(default_factory=list)
    
    message: Optional[Dict[str, Any]] = None
    
    user_input: str = ""
    
    intent: Optional[str] = None
    intents: List[Dict[str, Any]] = field(default_factory=list)
    
    user_needs: Optional[str] = None
    
    resource_types: Optional[List[str]] = field(default_factory=list)
    
    quantity_limit: Optional[int] = None
    
    grade_info: Optional[Dict[str, Any]] = None
    
    clarified_topic: Optional[Dict[str, Any]] = None
    
    retrieved_resources: Optional[Dict[str, Any]] = None
    
    lesson_plan_session_id: Optional[str] = None
    lesson_plan_status: Optional[str] = None
    lesson_plan_collected_info: Optional[Dict[str, Any]] = None
    lesson_plan: Optional[str] = None
    export_data: Optional[Dict[str, Any]] = None
    
    visualization_suggestions: Optional[str] = None
    
    ggb_design_suggestions: Optional[List[Dict[str, Any]]] = None
    
    search_results: Optional[str] = None
    
    response: Optional[str] = None

    response_mode: Optional[str] = None

    skip_retrieval: bool = False
    
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    
    error: Optional[str] = None
    
    current_step: Optional[str] = None
    
    context: Optional[Dict[str, Any]] = None
