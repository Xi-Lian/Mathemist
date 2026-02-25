#!/usr/bin/env python3
"""
检查幂函数习题与查询的相似度
"""

from app.core.vector_database_builder import VectorDatabaseBuilder
from pathlib import Path

if __name__ == "__main__":
    print("=== 检查幂函数习题与查询的相似度 ===")
    
    # 初始化向量数据库构建器
    current_dir = Path(__file__).parent.parent
    learning_resource_path = current_dir / 'learning_resource'
    vector_db_builder = VectorDatabaseBuilder(str(learning_resource_path))
    
    # 获取客户端和模型
    client = vector_db_builder.get_chroma_client()
    embedding_model = vector_db_builder.get_embedding_model()
    collection = client.get_collection(name="math_resources")
    
    # 生成查询向量
    query = "幂函数的习题"
    query_embedding = embedding_model.encode(
        [query], 
        normalize_embeddings=True
    ).tolist()
    
    print(f"\n查询: {query}")
    print(f"查询向量维度: {len(query_embedding[0])}")
    
    # 查询所有资源
    print("\n查询所有资源...")
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=200,
        include=["documents", "metadatas", "distances"]
    )
    
    print(f"\n查询返回 {len(results['documents'][0])} 条结果")
    
    # 查找幂函数相关资源
    print("\n查找幂函数相关资源...")
    power_function_resources = []
    for i, (doc, metadata, distance) in enumerate(zip(results['documents'][0], results['metadatas'][0], results['distances'][0])):
        source_file = metadata.get('source_file', '')
        resource_type = metadata.get('resource_type', '')
        if '幂函数' in source_file or '3-3' in source_file:
            relevance = 1 - distance
            power_function_resources.append((i, metadata, distance, relevance))
            print(f"\n{i+1}. 类型: {resource_type}, 源文件: {source_file}")
            print(f"   距离: {distance:.3f}, 相似度: {relevance:.1%}")
            print(f"   标题: {metadata.get('title', 'unknown')}")
            print(f"   知识点标签: {metadata.get('知识点标签', 'unknown')}")
    
    if not power_function_resources:
        print("\n❌ 查询结果中没有找到幂函数相关的资源")
    else:
        print(f"\n✅ 找到 {len(power_function_resources)} 个幂函数相关的资源")
