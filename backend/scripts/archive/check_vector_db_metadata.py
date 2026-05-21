#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查向量数据库中存储的复数相关资源的元数据
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查向量数据库中复数相关资源的元数据")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()
    collection = client.get_collection(name='math_resources_algebra')

    print(f"\n代数集合文档总数: {collection.count()}")

    # 获取所有资源
    results = collection.get(include=['metadatas', 'documents'])

    # 筛选复数相关的资源
    complex_resources = []
    for i, metadata in enumerate(results['metadatas']):
        title = metadata.get('title', '')
        source_file = metadata.get('source_file', '')
        if any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [title, source_file]):
            complex_resources.append({
                'id': results['ids'][i],
                'metadata': metadata,
                'document': results['documents'][i][:100] if results['documents'][i] else ''
            })

    print(f"\n代数集合中复数相关资源数: {len(complex_resources)}")

    # 显示前5个复数相关资源的完整元数据
    print(f"\n前5个复数相关资源的完整元数据：")
    for i, res in enumerate(complex_resources[:5]):
        print(f"\n  {i+1}. 标题: {res['metadata'].get('title', '未知')}")
        print(f"     资源类型: {res['metadata'].get('resource_type', '未知')}")
        print(f"     源文件: {res['metadata'].get('source_file', '未知')[:80]}...")
        print(f"     云端链接: {res['metadata'].get('cloud_url', '未知')[:80] if res['metadata'].get('cloud_url') else '无'}...")
        print(f"     原文件云端链接: {res['metadata'].get('original_file_url', '未知')[:80] if res['metadata'].get('original_file_url') else '无'}...")
        print(f"     原文件名: {res['metadata'].get('original_filename', '未知')}")

        # 打印所有可用的元数据键
        if i == 0:
            print(f"     可用的元数据键: {list(res['metadata'].keys())}")

    # 检查向量数据库中的资源是否缺少"原文件云端链接"
    print("\n" + "="*60)
    print("检查向量数据库元数据完整性")
    print("="*60)

    has_original_url = 0
    no_original_url = 0

    for res in complex_resources:
        if res['metadata'].get('original_file_url'):
            has_original_url += 1
        else:
            no_original_url += 1

    print(f"\n复数相关资源中：")
    print(f"  有原文件云端链接: {has_original_url}条")
    print(f"  无原文件云端链接: {no_original_url}条")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
