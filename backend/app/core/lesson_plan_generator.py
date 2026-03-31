"""
兼容入口：教案生成模块

实际实现已迁移到 `app.core.lesson_plan.generator`，保留此文件以兼容现有导入路径。
"""

from .lesson_plan.generator import LessonPlanGenerator, lesson_plan_generation_node

__all__ = ["LessonPlanGenerator", "lesson_plan_generation_node"]
