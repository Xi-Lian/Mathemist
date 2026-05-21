#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查教学大纲、GGB和课例视频资源的解析情况
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查教学大纲、GGB和课例视频资源")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))

    # 解析所有资源汇总表
    print("\n解析所有资源汇总表...")
    all_resources = builder.parser.parse_all_tables()

    # 检查教学大纲资源
    print("\n教学大纲资源：")
    if 'syllabus' in all_resources:
        print(f"  教学大纲资源数量: {len(all_resources['syllabus'])}条")
        for i, resource in enumerate(all_resources['syllabus'][:3]):
            print(f"  {i+1}. {resource.get('title', '未知')}")
            print(f"     源文件: {resource.get('source_file', '未知')}")
    else:
        print("  未找到教学大纲资源")

    # 检查GGB资源
    print("\nGGB资源：")
    if 'ggb' in all_resources:
        print(f"  GGB资源数量: {len(all_resources['ggb'])}条")
        for i, resource in enumerate(all_resources['ggb'][:3]):
            print(f"  {i+1}. {resource.get('title', '未知')}")
            print(f"     源文件: {resource.get('source_file', '未知')}")
    else:
        print("  未找到GGB资源")

    # 检查课例视频资源
    print("\n课例视频资源：")
    if 'lesson_case' in all_resources:
        print(f"  课例视频资源数量: {len(all_resources['lesson_case'])}条")
        # 检查是否有复数相关的课例视频
        complex_lesson_cases = []
        for resource in all_resources['lesson_case']:
            title = resource.get('title', '')
            source_file = resource.get('source_file', '')
            if any(keyword in text for keyword in ["复数", "虚数"] for text in [title, source_file]):
                complex_lesson_cases.append(resource)
        print(f"  复数相关课例视频数量: {len(complex_lesson_cases)}条")
        for i, resource in enumerate(complex_lesson_cases[:3]):
            print(f"  {i+1}. {resource.get('title', '未知')}")
            print(f"     源文件: {resource.get('source_file', '未知')}")
    else:
        print("  未找到课例视频资源")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
