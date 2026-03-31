"""
教案生成模块

职责：
- 根据用户需求和检索到的资源生成教案
- 整合理论依据和优秀教案特征
- 提供结构化的教案输出
- 明确标注理论依据的使用场景和作用

依赖：
- model_config (模型配置)
- langchain (提示词和链)
"""

from typing import Dict, Any, List
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ..model_config import model_config
from ..config_manager import config_manager


