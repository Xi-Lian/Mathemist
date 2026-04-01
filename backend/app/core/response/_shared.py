"""
响应生成模块

职责：
- 根据意图和生成的结果构建最终响应
- 整合教案、可视化建议和检索到的资源
- 提供结构化的响应输出
- V33.0改进：添加超时处理和降级方案

依赖：
- model_config (模型配置)
- smart_content_processor (内容处理)
"""

import builtins
import os
import time
from typing import Dict, Any, List
from ..model_config import model_config
from ...smart_content_processor import SmartContentProcessor
from ...config.resource_type_config import (
    get_response_field,
    get_icon,
    get_standard_name,
    get_resource_type_mapping
)

VERBOSE_LOGS = os.getenv("APP_VERBOSE_LOGS", "0").strip().lower() in {"1", "true", "yes", "on", "debug", "verbose"}


def print(*args, **kwargs):
    if VERBOSE_LOGS:
        builtins.print(*args, **kwargs)


