"""
资源检索模块

职责：
- 使用ChromaDB进行语义检索
- 根据查询和意图检索相关资源
- 对检索结果进行分类和组织
- 实现习题资源的特殊处理逻辑
- V33.0改进：支持数量限制、年级筛选、主题澄清

依赖：
- model_config (模型配置)
- resource_classifier (资源分类)
- vector_database_builder (向量数据库构建)
- resource_table_parser (资源汇总表解析)
- chromadb (向量数据库)
- sentence_transformers (Embedding模型)
"""

import builtins
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from ..model_config import model_config
from ..resource_classifier import ResourceClassifier
from ..vector_database_builder import VectorDatabaseBuilder
from ..resource_table_parser import ResourceTableParser
from ..theme_matcher import get_theme_matcher
from ..theme_matcher_v90 import get_theme_matcher_v90
from ..content_feature_extractor import get_content_feature_extractor
from ...config.resource_type_config import (
    get_db_type,
    get_resource_type_mapping,
    get_standard_name,
    get_all_user_types,
    get_all_db_types
)
from ...config.dynamic_config_loader import get_config_loader

VERBOSE_LOGS = os.getenv("APP_VERBOSE_LOGS", "0").strip().lower() in {"1", "true", "yes", "on", "debug", "verbose"}


def print(*args, **kwargs):
    if VERBOSE_LOGS:
        builtins.print(*args, **kwargs)


