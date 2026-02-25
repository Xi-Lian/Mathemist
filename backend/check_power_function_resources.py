#!/usr/bin/env python3
"""
检查向量数据库中是否包含幂函数的习题资源
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.vector_database_builder import VectorDatabaseBuilder


def check_power_function_resources():
    """
    检查向量数据库中是否包含幂函数的习题资源
    """
    print("\n" + "="*60)
    print("检查幂函数习题资源")
    print("="*60)
    
    try:
        # 初始化向量数据库构建器
        builder = VectorDatabaseBuilder('d:\\Git_Repository\\Mathemist\\learning_resource')
        
        # 获取ChromaDB客户端
        client = builder.get_chroma_client()
        
        # 获取集合
        collection = client.get_collection(name=builder.COLLECTION_NAME)
        
        # 查询包含幂函数的资源
        print("查询包含幂函数的资源...")
        results = collection.query(
            query_texts=["幂函数习题"],
            n_results=50,
            include=["documents", "metadatas", "distances"]
        )
        
        # 分析结果
        print(f"\n查询结果数量: {len(results['documents'][0])}")
        
        power_function_resources = []
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            source_file = metadata.get('source_file', '')
            resource_type = metadata.get('resource_type', '')
            title = metadata.get('title', '')
            
            # 检查是否是幂函数相关的习题
            if '幂函数' in source_file or '3-3' in source_file:
                power_function_resources.append({
                    'index': i+1,
                    'source_file': source_file,
                    'resource_type': resource_type,
                    'title': title,
                    'distance': distance,
                    'relevance': 1 - distance
                })
        
        if power_function_resources:
            print("\n找到幂函数相关资源:")
            for resource in power_function_resources:
                print(f"{resource['index']}. 类型: {resource['resource_type']}, 源文件: {resource['source_file']}, 相似度: {resource['relevance']:.1%}")
        else:
            print("\n❌ 未找到幂函数相关资源！")
            
        # 检查所有习题资源
        print("\n" + "-"*40)
        print("检查所有习题资源:")
        
        exercise_resources = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            resource_type = metadata.get('resource_type', '')
            if resource_type == 'exercise':
                exercise_resources.append({
                    'index': i+1,
                    'source_file': metadata.get('source_file', ''),
                    'title': metadata.get('title', ''),
                    'relevance': 1 - distance
                })
        
        print(f"找到习题资源数量: {len(exercise_resources)}")
        if exercise_resources:
            print("\n前10个习题资源:")
            for resource in exercise_resources[:10]:
                print(f"{resource['index']}. {resource['source_file']} - 相似度: {resource['relevance']:.1%}")
        
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_power_function_resources()
