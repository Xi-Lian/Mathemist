"""
检查GGB资源在向量数据库中的情况
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.vector_database_builder import VectorDatabaseBuilder

def check_ggb_resources():
    print("🔍 检查GGB资源...")
    
    builder = VectorDatabaseBuilder(str(backend_dir.parent / 'learning_resource'))
    
    # 获取数据库统计
    stats = builder.get_database_stats()
    print(f"📊 数据库统计:")
    print(f"   总记录数: {stats.get('total_count', 0)}")
    print(f"   类型统计: {stats.get('type_stats', {})}")
    
    # 获取所有GGB资源
    client = builder.get_chroma_client()
    collection = client.get_collection(name=builder.COLLECTION_NAME)
    
    results = collection.get(
        where={"resource_type": "ggb"},
        include=["documents", "metadatas"]
    )
    
    print(f"\n📋 GGB资源详情:")
    print(f"   GGB资源数量: {len(results['documents'])}")
    
    if results['documents']:
        print(f"\n   前5个GGB资源:")
        for i in range(min(5, len(results['documents']))):
            doc = results['documents'][i]
            metadata = results['metadatas'][i]
            print(f"\n   资源 {i+1}:")
            print(f"      文档: {doc[:100]}...")
            print(f"      元数据: {metadata}")
    
    return stats

if __name__ == "__main__":
    check_ggb_resources()
