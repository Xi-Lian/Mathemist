#!/usr/bin/env python3
"""
检查幂函数习题的元数据
"""

from app.core.vector_database_builder import VectorDatabaseBuilder
from pathlib import Path

if __name__ == "__main__":
    print("=== 检查幂函数习题的元数据 ===")
    
    # 初始化向量数据库构建器
    current_dir = Path(__file__).parent.parent
    learning_resource_path = current_dir / 'learning_resource'
    vector_db_builder = VectorDatabaseBuilder(str(learning_resource_path))
    
    # 获取客户端和模型
    client = vector_db_builder.get_chroma_client()
    embedding_model = vector_db_builder.get_embedding_model()
    collection = client.get_collection(name="math_resources")
    
    # 查询所有资源
    print("\n查询所有资源...")
    results = collection.get(
        include=["documents", "metadatas"]
    )
    
    print(f"\n总资源数量: {len(results['documents'])}")
    
    # 查找幂函数习题资源
    print("\n查找幂函数习题资源...")
    power_function_exercises = []
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        source_file = metadata.get('source_file', '')
        resource_type = metadata.get('resource_type', '')
        if ('幂函数' in source_file or '3-3' in source_file) and resource_type == 'exercise':
            power_function_exercises.append((i, metadata))
            print(f"\n{i+1}. 类型: {resource_type}, 源文件: {source_file}")
            print(f"   标题: {metadata.get('title', 'unknown')}")
            print(f"   知识点标签: {metadata.get('知识点标签', 'unknown')}")
            print(f"   章节: {metadata.get('章节', 'unknown')}")
            print(f"   题干: {metadata.get('题干', 'unknown')[:100]}...")
            print(f"   题目类型: {metadata.get('题目类型', 'unknown')}")
            print(f"   难度: {metadata.get('难度（1-5）', 'unknown')}")
            print(f"   题目文件名: {metadata.get('题目文件名', 'unknown')}")
    
    if not power_function_exercises:
        print("\n❌ 没有找到幂函数习题资源")
    else:
        print(f"\n✅ 找到 {len(power_function_exercises)} 个幂函数习题资源")
