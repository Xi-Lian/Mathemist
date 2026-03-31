"""
意图理解模块

职责：
- 分析用户输入，确定用户意图
- 支持基于LLM的意图识别
- 提供关键词匹配作为备用方案
- V33.0改进：添加数量限制提取、年级信息提取、主题精准识别

依赖：
- model_config (模型配置)
- langchain (提示词和链)

支持的意图类型：
- search: 资源搜索
- generate_lesson_plan: 教案生成
- visualization: 可视化建议
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ..model_config import model_config


