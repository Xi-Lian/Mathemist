"""
统一教案生成系统

核心理念：
- 不区分"协编"和"生成"模式
- 根据用户输入的完整程度智能决定处理方式
- 信息完整 → 直接生成完整教案
- 信息不完整 → 引导用户补充关键信息
- 支持多轮对话迭代优化
- 最终统一导出

职责：
- 智能分析用户输入的完整性
- 动态引导用户补充关键信息
- 整合理论资源和优秀案例
- 生成高质量教案
- 支持多格式导出

依赖：
- lesson_plan_generator (教案生成核心)
- lesson_plan_exporter (教案导出)
- resource_retriever (资源检索)
- model_config (模型配置)
"""

import os
import json
import time
import base64
import io
import zipfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
import uuid
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
from ..lesson_plan_generator import LessonPlanGenerator
from ..lesson_plan_exporter import (
    export_lesson_plan_markdown,
    export_lesson_plan_html,
    export_lesson_plan_docx,
    export_lesson_plan_pdf,
    export_lesson_plan_all
)
from ..resource_retriever import ResourceRetriever
from ..model_config import model_config
from ..config_manager import config_manager


class LessonPlanInfoCompletion(Enum):
    """教案信息完整度"""
    COMPLETE = "complete"  # 信息完整，可以直接生成
    PARTIAL = "partial"    # 信息部分完整，需要引导补充
    MINIMAL = "minimal"    # 信息很少，需要逐步引导


class RequiredInfo(BaseModel):
    """教案所需关键信息"""
    topic: str = Field(description="课题名称")
    teaching_goals: Optional[str] = Field(description="教学目标", default=None)
    teaching_methods: Optional[str] = Field(description="教学方法", default=None)
    student_level: Optional[str] = Field(description="学生水平", default=None)
    class_hours: Optional[str] = Field(description="课时", default=None)
    key_points: Optional[str] = Field(description="教学重点", default=None)
    difficulties: Optional[str] = Field(description="教学难点", default=None)


