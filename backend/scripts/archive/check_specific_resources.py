#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查特定资源的完整元数据
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("\n" + "="*60)
    print("检查特定资源的完整元数据")
    print("="*60)

    # 初始化向量数据库构建器
    builder = VectorDatabaseBuilder(os.path.join(os.path.dirname(__file__), '..', 'learning_resource'))
    client = builder.get_chroma_client()
    collection = client.get_collection(name='math_resources_probability')

    # 获取所有资源
    results = collection.get(include=['metadatas'])

    # 筛选特定资源
    specific_resources = []
    for i, metadata in enumerate(results['metadatas']):
        title = metadata.get('title', '')
        if any(keyword in title for keyword in [
            '公司员工的肥胖情况',
            '总体百分位数的估计 (2)',
            '总体百分位数的估计 (3)'
        ]):
            specific_resources.append({
                'id': results['ids'][i],
                'metadata': metadata
            })

    print(f"\n找到 {len(specific_resources)} 条特定资源")

    # 显示这些资源的完整元数据
    for i, res in enumerate(specific_resources):
        metadata = res['metadata']
        print(f"\n  {i+1}. 标题: {metadata.get('title', '未知')}")
        print(f"     资源类型: {metadata.get('resource_type', '未知')}")
        print(f"     源文件: {metadata.get('source_file', '未知')}")
        print(f"     云端链接: {metadata.get('云端链接', '未知')}")
        print(f"     原文件云端链接: {metadata.get('原文件云端链接', '未知')}")
        print(f"     原文件名: {metadata.get('原文件名', '未知')}")
        print(f"     完整路径: {metadata.get('完整路径', '未知')}")
        print(f"     知识点标签: {metadata.get('知识点标签', '未知')}")

        # 打印所有可用的元数据键
        if i == 0:
            print(f"     可用的元数据键: {list(metadata.keys())}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
