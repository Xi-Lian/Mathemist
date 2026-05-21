#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查未被识别为代数板块的复数相关教案
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查未被识别为代数板块的复数相关教案")
    print("="*60)
    
    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    
    # 解析所有资源汇总表
    print("解析所有资源汇总表...")
    all_resources = builder.parser.parse_all_tables()
    
    # 统计复数相关的资源
    complex_resources = {}
    for resource_type, resources in all_resources.items():
        for resource in resources:
            # 检查文件名、标题和路径是否包含复数相关关键词
            filename = resource.get('source_file', '').split('/')[-1]
            title = resource.get('title', '')
            source_file = resource.get('source_file', '')
            
            if any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [filename, title, source_file]):
                if resource_type not in complex_resources:
                    complex_resources[resource_type] = []
                complex_resources[resource_type].append(resource)
    
    # 检查未被识别为代数板块的教案
    print("\n未被识别为代数板块的复数相关教案：")
    if 'lesson_plan' in complex_resources:
        for resource in complex_resources['lesson_plan']:
            board = builder._get_resource_board(resource.get('source_file', ''), 'lesson_plan', resource.get('title', ''))
            if board != '代数':
                print(f"  - 标题: {resource.get('title', '未知')}")
                print(f"    文件名: {resource.get('source_file', '').split('/')[-1]}")
                print(f"    路径: {resource.get('source_file', '未知')}")
                print(f"    识别的板块: {board}")
                print()
    
    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
