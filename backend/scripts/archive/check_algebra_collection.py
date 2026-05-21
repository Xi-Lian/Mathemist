#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查代数集合中的资源类型分布
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查代数集合中的资源类型分布")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()
    collection = client.get_collection(name='math_resources_algebra')

    print(f"\n代数集合文档总数: {collection.count()}")

    # 获取所有资源
    results = collection.get(include=['metadatas'])

    # 统计资源类型分布
    type_counts = {}
    for metadata in results['metadatas']:
        resource_type = metadata.get('resource_type', '未知')
        if resource_type not in type_counts:
            type_counts[resource_type] = 0
        type_counts[resource_type] += 1

    print("\n资源类型分布:")
    for resource_type, count in type_counts.items():
        print(f"  - {resource_type}: {count}条")

    # 打印前10个资源的标题和类型
    print("\n前10个资源:")
    for i, metadata in enumerate(results['metadatas'][:10]):
        print(f"  {i+1}. {metadata.get('title', '未知')} ({metadata.get('resource_type', '未知')})")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
