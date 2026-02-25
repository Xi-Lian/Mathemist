#!/usr/bin/env python3
"""
检查幂函数习题的详细信息
"""

from app.core.vector_database_builder import VectorDatabaseBuilder
from pathlib import Path

if __name__ == "__main__":
    print("=== 检查幂函数习题的详细信息 ===")
    
    # 初始化向量数据库构建器
    current_dir = Path(__file__).parent.parent
    learning_resource_path = current_dir / 'learning_resource'
    vector_db_builder = VectorDatabaseBuilder(str(learning_resource_path))
    
    # 获取客户端和集合
    client = vector_db_builder.get_chroma_client()
    collection = client.get_collection(name="math_resources")
    
    # 查询所有资源
    print("\n查询所有资源...")
    results = collection.get(
        include=["documents", "metadatas"]
    )
    
    print(f"\n总资源数量: {len(results['documents'])}")
    
    # 查找幂函数相关资源
    print("\n查找幂函数相关资源...")
    power_function_resources = []
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        source_file = metadata.get('source_file', '')
        if '幂函数' in source_file or '3-3' in source_file:
            power_function_resources.append((i, metadata))
            print(f"\n{i+1}. 类型: {metadata.get('resource_type', 'unknown')}, 源文件: {source_file}")
            print(f"   标题: {metadata.get('title', 'unknown')}")
            print(f"   知识点标签: {metadata.get('知识点标签', 'unknown')}")
            print(f"   章节: {metadata.get('章节', 'unknown')}")
            print(f"   题干: {metadata.get('题干', 'unknown')[:100]}...")
    
    if not power_function_resources:
        print("\n❌ 没有找到幂函数相关的资源")
    else:
        print(f"\n✅ 找到 {len(power_function_resources)} 个幂函数相关的资源")
    
    # 查找所有习题资源
    print("\n查找所有习题资源...")
    exercise_resources = []
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        resource_type = metadata.get('resource_type', '')
        if resource_type == 'exercise':
            exercise_resources.append((i, metadata))
    
    print(f"\n找到 {len(exercise_resources)} 个习题资源")
    
    # 打印前10个习题资源
    print("\n前10个习题资源:")
    for i, (idx, metadata) in enumerate(exercise_resources[:10]):
        source_file = metadata.get('source_file', '')
        print(f"{i+1}. {source_file}")
