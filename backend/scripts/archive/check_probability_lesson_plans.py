#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查概率统计板块的教案资源的原文件云端链接
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("详细检查概率统计板块的教案资源")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()
    collection = client.get_collection(name='math_resources_probability')

    # 获取所有资源
    results = collection.get(include=['metadatas'])

    # 筛选教案资源
    lesson_plans = []
    for i, metadata in enumerate(results['metadatas']):
        if metadata.get('resource_type') == 'lesson_plan':
            lesson_plans.append({
                'id': results['ids'][i],
                'metadata': metadata
            })

    print(f"\n概率统计板块教案总数: {len(lesson_plans)}条")

    # 检查原文件云端链接
    has_original_url = 0
    no_original_url = 0
    problematic_resources = []

    for res in lesson_plans:
        original_url = res['metadata'].get('原文件云端链接', '')
        if original_url and original_url != '无':
            has_original_url += 1
        else:
            no_original_url += 1
            problematic_resources.append(res['metadata'])

    print(f"\n有原文件云端链接: {has_original_url}条")
    print(f"无原文件云端链接: {no_original_url}条")

    # 显示所有无原文件云端链接的资源
    if problematic_resources:
        print(f"\n无原文件云端链接的资源：")
        for i, metadata in enumerate(problematic_resources):
            print(f"  {i+1}. {metadata.get('title', '未知')[:60]}")
            print(f"     源文件: {metadata.get('source_file', '未知')}")
            print(f"     原文件云端链接: '{metadata.get('原文件云端链接', '无')}'")
            print()
    else:
        print("\n所有教案都有原文件云端链接！")

    # 随机检查10个有原文件云端链接的资源
    if has_original_url > 10:
        print("\n随机检查10个有原文件云端链接的资源：")
        import random
        sample = random.sample([r for r in lesson_plans if r['metadata'].get('原文件云端链接') and r['metadata'].get('原文件云端链接') != '无'], 10)
        for i, res in enumerate(sample):
            metadata = res['metadata']
            print(f"  {i+1}. {metadata.get('title', '未知')[:50]}")
            print(f"     原文件名: {metadata.get('原文件名', '未知')}")
            print(f"     原文件云端链接: {metadata.get('原文件云端链接', '无')[:100]}...")
            print()

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
