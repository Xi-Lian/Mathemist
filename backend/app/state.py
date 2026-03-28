from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

@dataclass
class MathAgentState:
    """高中数学资源智能体状态定义"""
    
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
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
    
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    
    error: Optional[str] = None
    
    current_step: Optional[str] = None
    
    context: Optional[Dict[str, Any]] = None
