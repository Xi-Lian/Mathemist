#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查教案资源的元数据，特别是云端链接信息
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查教案资源的元数据")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))

    # 解析所有资源汇总表
    print("\n解析所有资源汇总表...")
    all_resources = builder.parser.parse_all_tables()

    # 检查 lesson_plan 资源
    if 'lesson_plan' in all_resources:
        print(f"\nlesson_plan 资源总数: {len(all_resources['lesson_plan'])}")

        # 显示前5个资源的完整元数据
        print(f"\n前5个 lesson_plan 资源的完整元数据：")
        for i, resource in enumerate(all_resources['lesson_plan'][:5]):
            print(f"\n  {i+1}. 标题: {resource.get('title', '未知')}")
            print(f"     资源类型: {resource.get('resource_type', '未知')}")
            print(f"     源文件: {resource.get('source_file', '未知')[:80]}...")
            print(f"     完整路径: {resource.get('完整路径', '未知')[:80]}..." if resource.get('完整路径') else "     完整路径: 无")
            print(f"     云端链接: {resource.get('云端链接', '未知')[:80]}..." if resource.get('云端链接') else "     云端链接: 无")
            print(f"     知识点标签: {resource.get('知识点标签', '未知')}")

            # 检查所有可用的元数据键
            if i == 0:
                print(f"     可用的元数据键: {list(resource.keys())}")

    # 检查复数相关的 lesson_plan 资源
    print("\n" + "="*60)
    print("检查复数相关的 lesson_plan 资源")
    print("="*60)

    if 'lesson_plan' in all_resources:
        complex_resources = []
        for resource in all_resources['lesson_plan']:
            source_file = resource.get('source_file', '')
            if "复数" in source_file or "虚数" in source_file:
                complex_resources.append(resource)

        print(f"\n复数相关的 lesson_plan 资源总数: {len(complex_resources)}")

        # 显示前3个复数相关资源的元数据
        print(f"\n前3个复数相关 lesson_plan 资源的完整元数据：")
        for i, resource in enumerate(complex_resources[:3]):
            print(f"\n  {i+1}. 标题: {resource.get('title', '未知')}")
            print(f"     源文件: {resource.get('source_file', '未知')}")
            print(f"     完整路径: {resource.get('完整路径', '未知')}")
            print(f"     云端链接: {resource.get('云端链接', '未知')}")
            print(f"     知识点标签: {resource.get('知识点标签', '未知')}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
