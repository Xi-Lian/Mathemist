"""
检查棱柱课件在数据库中的完整元数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

def check_prism_metadata():
    """检查棱柱课件的元数据"""
    
    print("=" * 80)
    print("检查棱柱课件在数据库中的完整元数据")
    print("=" * 80)
    
    learning_resource_path = os.path.join(os.path.dirname(__file__), 'learning_resource')
    vdb_builder = VectorDatabaseBuilder(learning_resource_path)
    client = vdb_builder.get_chroma_client()
    
    collection_name = "math_resources_geometry"
    collection = client.get_collection(name=collection_name)
    
    # 获取所有课件
    results = collection.get(
        where={"resource_type": "courseware"},
        include=["metadatas", "documents"]
    )
    
    print(f"\n总课件数: {len(results['ids'])}\n")
    
    # 查找目标课件
    for doc_id, metadata, document in zip(results['ids'], results['metadatas'], results['documents']):
        filename = metadata.get('文件名', '')
        
        if '课时1' in filename and '棱柱' in filename:
            print("-" * 80)
            print("【目标课件1】")
            print("-" * 80)
            print(f"ID: {doc_id}")
            print(f"文件名: {filename}")
            print(f"教学用途: {metadata.get('教学用途', '')}")
            print(f"知识点: {metadata.get('知识点', '')}")
            print(f"章节: {metadata.get('章节', '')}")
            print(f"年级: {metadata.get('年级', '')}")
            print(f"内容长度: {len(metadata.get('内容', '') or document or '')}")
            print(f"内容预览 (前200字): {(metadata.get('内容', '') or document or '')[:200]}")
            print()
        
        if '课时2' in filename and ('圆柱' in filename or '棱柱' in filename):
            print("-" * 80)
            print("【目标课件2】")
            print("-" * 80)
            print(f"ID: {doc_id}")
            print(f"文件名: {filename}")
            print(f"教学用途: {metadata.get('教学用途', '')}")
            print(f"知识点: {metadata.get('知识点', '')}")
            print(f"章节: {metadata.get('章节', '')}")
            print(f"年级: {metadata.get('年级', '')}")
            print(f"内容长度: {len(metadata.get('内容', '') or document or '')}")
            print(f"内容预览 (前200字): {(metadata.get('内容', '') or document or '')[:200]}")
            print()

if __name__ == "__main__":
    check_prism_metadata()
