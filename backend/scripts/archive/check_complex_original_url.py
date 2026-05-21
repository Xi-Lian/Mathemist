#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查复数相关资源的原文件云端链接
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("详细检查复数相关资源的原文件云端链接")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()
    collection = client.get_collection(name='math_resources_algebra')

    # 获取所有资源
    results = collection.get(include=['metadatas'])

    # 筛选复数相关的资源
    complex_resources = []
    for i, metadata in enumerate(results['metadatas']):
        title = metadata.get('title', '')
        source_file = metadata.get('source_file', '')
        if any(keyword in text for keyword in ["复数", "虚数", "数系扩充", "复平面", "共轭复数"] for text in [title, source_file]):
            complex_resources.append({
                'id': results['ids'][i],
                'metadata': metadata
            })

    print(f"\n代数集合中复数相关资源数: {len(complex_resources)}")

    # 显示前5个复数相关资源的完整元数据
    print(f"\n前5个复数相关资源的原文件云端链接：")
    for i, res in enumerate(complex_resources[:5]):
        metadata = res['metadata']
        original_url = metadata.get('原文件云端链接', '')
        original_filename = metadata.get('原文件名', '')

        print(f"\n  {i+1}. 标题: {metadata.get('title', '未知')[:50]}")
        print(f"     原文件云端链接: {original_url}")
        print(f"     原文件名: {original_filename}")
        print(f"     链接长度: {len(original_url) if original_url else 0}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
