#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查向量数据库中复数教案的实际板块分布
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查向量数据库中复数教案的实际板块分布")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()

    # 检查代数集合
    print("\n代数集合中的教案：")
    try:
        algebra_collection = client.get_collection(name='math_resources_algebra')
        print(f"  代数集合总数: {algebra_collection.count()}")

        # 获取所有教案
        results = algebra_collection.get(
            where={"resource_type": "lesson_plan"},
            include=['metadatas']
        )

        print(f"  代数集合中的教案数量: {len(results['metadatas'])}")

        # 检查标题中包含"复数"的教案
        complex_plans = []
        for metadata in results['metadatas']:
            title = metadata.get('title', '')
            if '复数' in title or '几何意义' in title:
                complex_plans.append(metadata)

        print(f"  标题包含'复数'或'几何意义'的教案: {len(complex_plans)}")

        # 显示前5个
        if complex_plans:
            print("\n  前5个复数相关教案：")
            for i, meta in enumerate(complex_plans[:5]):
                print(f"    {i+1}. {meta.get('title', '未知')}")
                print(f"       源文件: {meta.get('source_file', '未知')[:80]}...")

    except Exception as e:
        print(f"  获取代数集合失败: {e}")

    # 检查几何集合
    print("\n几何集合中的教案：")
    try:
        geometry_collection = client.get_collection(name='math_resources_geometry')
        print(f"  几何集合总数: {geometry_collection.count()}")

        # 获取所有教案
        results = geometry_collection.get(
            where={"resource_type": "lesson_plan"},
            include=['metadatas']
        )

        print(f"  几何集合中的教案数量: {len(results['metadatas'])}")

        # 检查标题中包含"复数"的教案
        complex_plans = []
        for metadata in results['metadatas']:
            title = metadata.get('title', '')
            if '复数' in title or '几何意义' in title:
                complex_plans.append(metadata)

        print(f"  标题包含'复数'或'几何意义'的教案: {len(complex_plans)}")

        # 显示前5个
        if complex_plans:
            print("\n  前5个复数相关教案：")
            for i, meta in enumerate(complex_plans[:5]):
                print(f"    {i+1}. {meta.get('title', '未知')}")
                print(f"       源文件: {meta.get('source_file', '未知')[:80]}...")

    except Exception as e:
        print(f"  获取几何集合失败: {e}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
