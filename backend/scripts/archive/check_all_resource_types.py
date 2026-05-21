#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有资源类型中是否还有复数相关内容被遗漏
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查所有资源类型中是否还有复数相关内容被遗漏")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))

    # 解析所有资源汇总表
    print("\n解析所有资源汇总表...")
    all_resources = builder.parser.parse_all_tables()

    # 打印所有资源类型
    print("\n所有资源类型：")
    for resource_type, resources in all_resources.items():
        print(f"  - {resource_type}: {len(resources)}条")

    # 检查是否有复数相关内容在 lesson_case 或其他类型中
    print("\n检查 lesson_case（课例视频）中是否有复数相关内容：")
    if 'lesson_case' in all_resources:
        complex_in_lesson_case = []
        for resource in all_resources['lesson_case']:
            filename = resource.get('source_file', '').split('/')[-1]
            title = resource.get('title', '')
            source_file = resource.get('source_file', '')

            if any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [filename, title, source_file]):
                complex_in_lesson_case.append(resource)

        print(f"  找到 {len(complex_in_lesson_case)} 条复数相关的课例视频")
        if complex_in_lesson_case:
            for i, res in enumerate(complex_in_lesson_case[:5]):
                print(f"    {i+1}. {res.get('title', '未知')}")
                print(f"       路径: {res.get('source_file', '未知')[:80]}...")

    # 检查数据库中代数集合的完整内容
    print("\n检查数据库中代数集合的完整内容：")
    client = builder.get_chroma_client()
    try:
        collection = client.get_collection(name='math_resources_algebra')
        print(f"  代数集合总数: {collection.count()}")

        # 获取所有资源的类型分布
        results = collection.get(include=['metadatas'])
        type_counts = {}
        for metadata in results['metadatas']:
            resource_type = metadata.get('resource_type', '未知')
            if resource_type not in type_counts:
                type_counts[resource_type] = 0
            type_counts[resource_type] += 1

        print(f"  类型分布：")
        for rt, count in type_counts.items():
            print(f"    - {rt}: {count}条")

    except Exception as e:
        print(f"  获取代数集合失败: {e}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
