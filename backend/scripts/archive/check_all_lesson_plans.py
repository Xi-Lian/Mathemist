#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有板块的教案资源的原文件云端链接
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查所有板块的教案资源的原文件云端链接")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()

    # 检查所有板块集合
    collections_to_check = [
        ('math_resources_algebra', '代数'),
        ('math_resources_geometry', '几何'),
        ('math_resources_function', '函数'),
        ('math_resources_probability', '概率统计'),
        ('math_resources_general', '通用')
    ]

    for collection_name, board_name in collections_to_check:
        try:
            collection = client.get_collection(name=collection_name)
            print(f"\n{board_name}板块 ({collection_name}): {collection.count()}条")

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

            if lesson_plans:
                print(f"  教案数量: {len(lesson_plans)}条")

                # 检查原文件云端链接
                has_original_url = 0
                no_original_url = 0
                sample_with_url = []
                sample_without_url = []

                for res in lesson_plans:
                    original_url = res['metadata'].get('原文件云端链接', '')
                    if original_url and original_url != '无':
                        has_original_url += 1
                        if len(sample_with_url) < 2:
                            sample_with_url.append(res['metadata'])
                    else:
                        no_original_url += 1
                        if len(sample_without_url) < 2:
                            sample_without_url.append(res['metadata'])

                print(f"  有原文件云端链接: {has_original_url}条")
                print(f"  无原文件云端链接: {no_original_url}条")

                if sample_with_url:
                    print(f"\n  有原文件云端链接的教案示例：")
                    for i, metadata in enumerate(sample_with_url[:2]):
                        print(f"    {i+1}. {metadata.get('title', '未知')[:50]}")
                        print(f"       原文件名: {metadata.get('原文件名', '未知')}")
                        print(f"       链接: {metadata.get('原文件云端链接', '无')[:80]}...")

                if sample_without_url:
                    print(f"\n  无原文件云端链接的教案示例：")
                    for i, metadata in enumerate(sample_without_url[:2]):
                        print(f"    {i+1}. {metadata.get('title', '未知')[:50]}")
                        print(f"       源文件: {metadata.get('source_file', '未知')[:80]}")

        except Exception as e:
            print(f"\n{board_name}板块: 获取失败 - {e}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
