"""
检查棱柱课件的向量检索情况
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

def check_prism_vector_search():
    """检查棱柱课件的向量检索"""
    
    print("=" * 80)
    print("检查棱柱课件的向量检索")
    print("=" * 80)
    
    # 创建VectorDatabaseBuilder实例
    learning_resource_path = os.path.join(os.path.dirname(__file__), 'learning_resource')
    vdb_builder = VectorDatabaseBuilder(learning_resource_path)
    client = vdb_builder.get_chroma_client()
    embedding_model = vdb_builder.get_embedding_model()
    
    collection_name = "math_resources_geometry"
    collection = client.get_collection(name=collection_name)
    
    # 生成查询向量
    query = "我想要棱柱的练习课课件"
    query_embedding = embedding_model.encode([query])[0].tolist()
    
    print(f"\n查询: {query}")
    print(f"集合: {collection_name}")
    print(f"执行向量检索...\n")
    
    # 执行向量检索
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=20,  # 取前20个
        include=["metadatas", "documents", "distances"]
    )
    
    print(f"返回 {len(results['ids'][0])} 个结果\n")
    print("-" * 80)
    
    # 检查是否包含目标课件
    target_found_1 = False
    target_found_2 = False
    
    for i, (doc_id, metadata, document, distance) in enumerate(zip(
        results['ids'][0],
        results['metadatas'][0],
        results['documents'][0],
        results['distances'][0]
    )):
        filename = metadata.get('文件名', '')
        teaching_use = metadata.get('教学用途', '')
        
        # 检查是否是目标课件
        is_target_1 = '课时1' in filename and '棱柱' in filename
        is_target_2 = '课时2' in filename and ('圆柱' in filename or '棱柱' in filename)
        
        if is_target_1:
            target_found_1 = True
            print(f"{i+1}. [TARGET 1] 文件名: {filename}")
        elif is_target_2:
            target_found_2 = True
            print(f"{i+1}. [TARGET 2] 文件名: {filename}")
        else:
            print(f"{i+1}. 文件名: {filename}")
        
        print(f"   教学用途: {teaching_use}")
        print(f"   向量距离: {distance:.4f}")
        print(f"   资源类型: {metadata.get('resource_type', 'N/A')}")
        print()
    
    print("=" * 80)
    print("结论:")
    print("=" * 80)
    if target_found_1:
        print("[OK] 目标课件1在向量检索结果中")
    else:
        print("[FAIL] 目标课件1不在向量检索结果前20名中")
    
    if target_found_2:
        print("[OK] 目标课件2在向量检索结果中")
    else:
        print("[FAIL] 目标课件2不在向量检索结果前20名中")
    
    if not target_found_1 or not target_found_2:
        print("\n可能原因:")
        print("  1. 向量嵌入质量不高，导致相似度低")
        print("  2. 课件内容字段太短（只有标题），向量表示不够丰富")
        print("  3. 查询向量与课件向量的语义距离较远")

if __name__ == "__main__":
    check_prism_vector_search()
