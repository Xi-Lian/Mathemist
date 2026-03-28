#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重建向量数据库
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

def rebuild_vector_db():
    """
    重建向量数据库
    """
    print("=" * 80)
    print("重建向量数据库")
    print("=" * 80)
    
    # 初始化向量数据库构建器
    current_dir = os.path.abspath(os.path.dirname(__file__))
    learning_resource_path = os.path.join(current_dir, 'learning_resource')
    builder = VectorDatabaseBuilder(learning_resource_path)
    
    # 强制重建数据库
    print("开始重建向量数据库...")
    success = builder.build_vector_database(force_rebuild=True)
    
    if success:
        print("✅ 向量数据库重建成功！")
    else:
        print("❌ 向量数据库重建失败！")

if __name__ == "__main__":
    rebuild_vector_db()
