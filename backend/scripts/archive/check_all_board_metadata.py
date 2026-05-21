#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有板块集合中的元数据完整性
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查所有板块集合中的元数据完整性")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()

    # 检查所有板块集合
    collections_to_check = [
        'math_resources_algebra',
        'math_resources_geometry',
        'math_resources_function',
        'math_resources_probability',
        'math_resources_general'
    ]

    for collection_name in collections_to_check:
        try:
            collection = client.get_collection(name=collection_name)
            print(f"\n{collection_name}: {collection.count()}条")

            # 获取前3个资源的元数据
            results = collection.get(include=['metadatas'], limit=3)

            for i, metadata in enumerate(results['metadatas'][:3]):
                has_original_url = bool(metadata.get('原文件云端链接') and metadata.get('原文件云端链接') != '无')
                print(f"  {i+1}. {metadata.get('title', '未知')[:40]}...")
                print(f"     原文件云端链接: {'有' if has_original_url else '无'}")

        except Exception as e:
            print(f"\n{collection_name}: 获取失败 - {e}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
