#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查习题资源的详细情况
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查习题资源的详细情况")
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

    # 检查 exercise 资源
    print("\n检查 exercise 类型资源：")
    if 'exercise' in all_resources:
        print(f"  exercise 资源总数: {len(all_resources['exercise'])}条")

        # 打印前5个 exercise 资源的详细信息
        print(f"\n  前5个 exercise 资源：")
        for i, resource in enumerate(all_resources['exercise'][:5]):
            print(f"    {i+1}. 标题: {resource.get('title', '未知')}")
            print(f"       源文件: {resource.get('source_file', '未知')[:80]}...")
            print(f"       知识点标签: {resource.get('知识点标签', '未知')}")
            print()
    else:
        print("  未找到 exercise 类型资源")

    # 检查所有包含"立体几何"或"复数"相关关键词的资源
    print("\n检查所有包含关键词的资源：")
    all_keywords = {}

    for resource_type, resources in all_resources.items():
        for resource in resources:
            source_file = resource.get('source_file', '')

            # 检查是否包含立体几何相关关键词
            if "立体几何" in source_file:
                if '立体几何' not in all_keywords:
                    all_keywords['立体几何'] = {'total': 0, 'types': {}}
                all_keywords['立体几何']['total'] += 1
                if resource_type not in all_keywords['立体几何']['types']:
                    all_keywords['立体几何']['types'][resource_type] = 0
                all_keywords['立体几何']['types'][resource_type] += 1

            # 检查是否包含复数相关关键词
            if any(kw in source_file for kw in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"]):
                if '复数' not in all_keywords:
                    all_keywords['复数'] = {'total': 0, 'types': {}}
                all_keywords['复数']['total'] += 1
                if resource_type not in all_keywords['复数']['types']:
                    all_keywords['复数']['types'][resource_type] = 0
                all_keywords['复数']['types'][resource_type] += 1

    for keyword, info in all_keywords.items():
        print(f"\n  {keyword}相关资源：")
        print(f"    总数: {info['total']}条")
        print(f"    类型分布：")
        for rt, count in info['types'].items():
            print(f"      - {rt}: {count}条")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
