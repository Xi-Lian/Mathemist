#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查立体几何相关表格中的复数相关内容
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查立体几何相关表格中的复数相关内容")
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

    # 重点检查立体几何相关的资源
    print("\n检查立体几何相关表格中是否包含复数内容：")

    # 检查各个类型的资源
    for resource_type, resources in all_resources.items():
        # 检查文件名、标题或路径是否包含"立体几何"
        stereoscopic_resources = []
        for resource in resources:
            filename = resource.get('source_file', '').split('/')[-1]
            title = resource.get('title', '')
            source_file = resource.get('source_file', '')

            # 如果路径中包含"立体几何"但不是复数相关的
            if "立体几何" in source_file:
                # 检查是否是复数相关的
                is_complex = any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [filename, title, source_file])

                stereoscopic_resources.append({
                    'title': title,
                    'filename': filename,
                    'source_file': source_file,
                    'is_complex': is_complex
                })

        if stereoscopic_resources:
            complex_count = sum(1 for r in stereoscopic_resources if r['is_complex'])
            non_complex_count = len(stereoscopic_resources) - complex_count

            print(f"\n  {resource_type}:")
            print(f"    立体几 何相关总数: {len(stereoscopic_resources)}条")
            print(f"    其中复数相关: {complex_count}条")
            print(f"    其中非复数相关: {non_complex_count}条")

            # 显示前3个非复数的立体几何资源
            non_complex_samples = [r for r in stereoscopic_resources if not r['is_complex']][:3]
            if non_complex_samples:
                print(f"    非复数的立体几何资源示例：")
                for i, r in enumerate(non_complex_samples):
                    print(f"      {i+1}. {r['title']}")
                    print(f"         文件名: {r['filename']}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
