"""
检查向量数据库中的课例资源
"""

import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from app.core.vector_database_builder import VectorDatabaseBuilder

def check_lesson_case_in_db():
    """检查向量数据库中的课例资源"""
    
    print("=" * 80)
    print("检查向量数据库中的课例资源")
    print("=" * 80)
    
    # 初始化向量数据库构建器
    learning_resource_path = Path(__file__).parent / 'learning_resource'
    vector_db_builder = VectorDatabaseBuilder(str(learning_resource_path))
    
    # 获取ChromaDB客户端
    client = vector_db_builder.get_chroma_client()
    
    # 获取集合
    collection = client.get_collection(name=vector_db_builder.COLLECTION_NAME)
    
    # 获取集合中的所有记录
    print("\n📊 获取集合中的所有记录...")
    all_results = collection.get(include=['metadatas', 'documents'])
    
    print(f"✅ 集合中共有{len(all_results['ids'])}条记录")
    
    # 统计各类资源的数量
    resource_type_count = {}
    for metadata in all_results['metadatas']:
        resource_type = metadata.get('resource_type', 'unknown')
        resource_type_count[resource_type] = resource_type_count.get(resource_type, 0) + 1
    
    print("\n各类资源数量:")
    for resource_type, count in resource_type_count.items():
        print(f"  - {resource_type}: {count}条")
    
    # 查找课例资源
    print("\n🔍 查找课例资源...")
    lesson_case_ids = []
    lesson_case_metadatas = []
    lesson_case_documents = []
    
    for i, metadata in enumerate(all_results['metadatas']):
        if metadata.get('resource_type') == 'lesson_case':
            lesson_case_ids.append(all_results['ids'][i])
            lesson_case_metadatas.append(metadata)
            lesson_case_documents.append(all_results['documents'][i])
    
    print(f"✅ 找到{len(lesson_case_ids)}条课例资源")
    
    if lesson_case_metadatas:
        print("\n前5条课例资源:")
        for i in range(min(5, len(lesson_case_metadatas))):
            print(f"\n{i+1}. ID: {lesson_case_ids[i]}")
            print(f"   元数据: {lesson_case_metadatas[i]}")
            print(f"   文档: {lesson_case_documents[i][:100]}...")
    
    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)

if __name__ == "__main__":
    check_lesson_case_in_db()
