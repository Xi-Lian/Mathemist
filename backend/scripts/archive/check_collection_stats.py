#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查向量数据库各集合的资源类型分布
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder


def check_collection_stats():
    """检查各集合的资源类型分布"""
    print("\n=== 检查向量数据库集合统计 ===")
    
    # 初始化构建器
    builder = VectorDatabaseBuilder("../learning_resource")
    client = builder.get_chroma_client()
    
    # 列出所有集合
    collections = client.list_collections()
    print("当前存在的集合:")
    for col in collections:
        print(f"- {col.name}")
    
    # 检查每个集合的资源类型分布
    collection_names = [
        "math_resources_function",
        "math_resources_geometry", 
        "math_resources_probability",
        "math_resources_algebra",
        "math_resources_general"
    ]
    
    for collection_name in collection_names:
        try:
            collection = client.get_collection(name=collection_name)
            count = collection.count()
            print(f"\n=== 集合: {collection_name} (共 {count} 条记录) ===")
            
            # 获取所有资源的元数据
            results = collection.get(include=['metadatas'])
            type_stats = {}
            
            for metadata in results['metadatas']:
                resource_type = metadata.get('resource_type', 'unknown')
                type_stats[resource_type] = type_stats.get(resource_type, 0) + 1
            
            print("资源类型分布:")
            for resource_type, count in type_stats.items():
                print(f"  - {resource_type}: {count} 条")
            
        except Exception as e:
            print(f"集合 {collection_name} 不存在: {str(e)}")


def check_lesson_plan_resources():
    """检查教案资源"""
    print("\n=== 检查教案资源 ===")
    
    # 初始化构建器
    builder = VectorDatabaseBuilder("../learning_resource")
    client = builder.get_chroma_client()
    
    # 检查每个集合中的教案资源
    collection_names = [
        "math_resources_function",
        "math_resources_geometry", 
        "math_resources_probability",
        "math_resources_algebra",
        "math_resources_general"
    ]
    
    for collection_name in collection_names:
        try:
            collection = client.get_collection(name=collection_name)
            
            # 执行查询，查找教案资源
            results = collection.query(
                query_texts=["教案"],
                n_results=10,
                where={"resource_type": "lesson_plan"},
                include=["metadatas"]
            )
            
            if results.get("metadatas") and results["metadatas"][0]:
                print(f"\n集合 {collection_name} 中的教案资源:")
                for i, meta in enumerate(results["metadatas"][0]):
                    title = meta.get('title', '未知标题')
                    source_file = meta.get('source_file', '未知来源')
                    print(f"  [{i+1}] {title} (来源: {source_file})")
            else:
                print(f"\n集合 {collection_name} 中没有教案资源")
            
        except Exception as e:
            print(f"集合 {collection_name} 不存在: {str(e)}")


if __name__ == "__main__":
    print("开始检查向量数据库集合统计...")
    
    # 检查各集合的资源类型分布
    check_collection_stats()
    
    # 检查教案资源
    check_lesson_plan_resources()
    
    print("\n检查完成!")
