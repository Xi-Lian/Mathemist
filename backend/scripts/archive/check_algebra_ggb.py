#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查代数板块的GGB资源
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查代数板块的GGB资源")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()

    # 获取代数板块集合
    collection = client.get_collection(name='math_resources_algebra')

    # 查询代数板块中的GGB资源
    results = collection.get(
        where={"resource_type": "ggb"},
        include=["metadatas"]
    )

    print(f"代数板块中的GGB资源数量: {len(results['metadatas'])}")

    # 打印每个GGB资源的详细信息
    for i, metadata in enumerate(results['metadatas']):
        print(f"\n{i+1}. 标题: {metadata.get('title', '未知')}")
        print(f"   源文件: {metadata.get('source_file', '未知')}")
        print(f"   章节: {metadata.get('章节', '未知')}")
        print(f"   ggb文件名: {metadata.get('ggb文件名', '未知')}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
