#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全面检查所有复数相关资源的归类情况
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("全面检查所有复数相关资源的归类情况")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))

    # 解析所有资源汇总表
    print("\n解析所有资源汇总表...")
    all_resources = builder.parser.parse_all_tables()

    # 找出所有复数相关的资源（通过文件名、标题或路径）
    all_complex_resources = {}
    for resource_type, resources in all_resources.items():
        for resource in resources:
            filename = resource.get('source_file', '').split('/')[-1]
            title = resource.get('title', '')
            source_file = resource.get('source_file', '')

            if any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [filename, title, source_file]):
                if resource_type not in all_complex_resources:
                    all_complex_resources[resource_type] = []
                all_complex_resources[resource_type].append(resource)

    # 打印所有复数相关资源统计
    print("\n所有复数相关资源统计：")
    total_complex = 0
    for resource_type, resources in all_complex_resources.items():
        print(f"  - {resource_type}: {len(resources)}条")
        total_complex += len(resources)
    print(f"  总计: {total_complex}条")

    # 检查这些资源是否被正确归类到代数板块
    print("\n检查资源归类情况：")
    for resource_type, resources in all_complex_resources.items():
        correct_board = 0
        wrong_board = 0
        wrong_resources = []

        for resource in resources:
            board = builder._get_resource_board(resource.get('source_file', ''), resource_type, resource.get('title', ''))
            if board == '代数':
                correct_board += 1
            else:
                wrong_board += 1
                wrong_resources.append({
                    'title': resource.get('title', '未知'),
                    'filename': resource.get('source_file', '').split('/')[-1],
                    'board': board
                })

        print(f"\n  {resource_type}:")
        print(f"    正确归类到代数: {correct_board}条")
        print(f"    错误归类到其他板块: {wrong_board}条")

        if wrong_resources:
            print(f"    错误归类的资源：")
            for i, res in enumerate(wrong_resources[:5]):  # 只显示前5个
                print(f"      {i+1}. {res['title']}")
                print(f"         文件名: {res['filename']}")
                print(f"         归类到: {res['board']}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
