import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.vector_database_builder import VectorDatabaseBuilder
from pathlib import Path

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 初始化向量数据库构建器
lr_path = Path("d:/Git_Repository/Mathemist/learning_resource")
builder = VectorDatabaseBuilder(str(lr_path))

# 构建向量数据库
builder.build_vector_database(force_rebuild=True)
