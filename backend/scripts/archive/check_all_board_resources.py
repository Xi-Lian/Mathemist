#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查所有板块的资源类型分布
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查所有板块的资源类型分布")
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

    # 存储所有板块的资源类型分布
    all_distributions = {}

    for collection_name, board_name in collections_to_check:
        try:
            collection = client.get_collection(name=collection_name)
            print(f"\n{board_name}板块 ({collection_name}):")

            # 获取所有资源
            results = collection.get(include=['metadatas'])

            # 统计资源类型分布
            type_distribution = {}
            for metadata in results['metadatas']:
                resource_type = metadata.get('resource_type', '未知')
                if resource_type not in type_distribution:
                    type_distribution[resource_type] = 0
                type_distribution[resource_type] += 1

            # 打印资源类型分布
            total = len(results['metadatas'])
            print(f"  总计: {total}条")
            for resource_type, count in type_distribution.items():
                print(f"  - {resource_type}: {count}条")

            # 存储分布信息
            all_distributions[board_name] = {
                'total': total,
                'distribution': type_distribution
            }

        except Exception as e:
            print(f"\n{board_name}板块: 获取失败 - {e}")

    # 打印汇总信息
    print("\n" + "="*60)
    print("资源类型分布汇总")
    print("="*60)

    for board_name, info in all_distributions.items():
        print(f"\n{board_name}板块:")
        print(f"  总计: {info['total']}条")
        for resource_type, count in info['distribution'].items():
            print(f"  - {resource_type}: {count}条")

    # 计算总体统计
    total_all = 0
    total_by_type = {}
    for info in all_distributions.values():
        total_all += info['total']
        for resource_type, count in info['distribution'].items():
            if resource_type not in total_by_type:
                total_by_type[resource_type] = 0
            total_by_type[resource_type] += count

    print("\n" + "="*60)
    print("总体统计")
    print("="*60)
    print(f"\n所有板块总计: {total_all}条")
    for resource_type, count in total_by_type.items():
        print(f"- {resource_type}: {count}条")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
