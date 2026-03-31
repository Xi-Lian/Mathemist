"""
用户系统和备课历史记录模块

职责：
- 用户身份管理和认证
- 备课历史记录的存储和检索
- 个人备课数据的管理
- 支持用户个性化配置

依赖：
- json (数据持久化)
- pathlib (路径管理)
- datetime (时间戳)
- uuid (生成唯一ID)
"""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum


class LessonPlanStatus(Enum):
    """教案状态"""
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class User:
    """用户数据模型"""
    user_id: str
    username: str
    email: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    preferences: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        return cls(**data)


@dataclass
class LessonPlanHistory:
    """备课历史记录"""
    history_id: str
    user_id: str
    topic: str
    chapter: Optional[str] = None
    textbook: Optional[str] = None
    teaching_goals: Optional[str] = None
    teaching_framework: Optional[str] = None
    lesson_plan_content: Optional[str] = None
    status: str = LessonPlanStatus.DRAFT.value
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LessonPlanHistory':
        return cls(**data)


