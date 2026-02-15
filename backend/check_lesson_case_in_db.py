import chromadb
from pathlib import Path

# 连接到向量数据库
db_path = Path("d:/Git_Repository/Mathemist/backend/app/data/chroma_db")
client = chromadb.PersistentClient(path=str(db_path))

# 列出所有集合
collections = client.list_collections()
print(f"向量数据库中的集合: {[col.name for col in collections]}")

if collections:
    # 获取第一个集合
    collection = collections[0]
    
    # 获取集合中的所有资源
    all_results = collection.get(
        include=["documents", "metadatas"]
    )
    
    print(f"\n集合名称: {collection.name}")
    print(f"总资源数量: {len(all_results['ids'])}")
    
    # 统计各类型资源数量
    resource_types = {}
    for metadata in all_results['metadatas']:
        resource_type = metadata.get('resource_type', 'unknown')
        resource_types[resource_type] = resource_types.get(resource_type, 0) + 1
    
    print("\n各类型资源统计:")
    for resource_type, count in sorted(resource_types.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {resource_type}: {count}个")
    
    # 查询课例资源
    lesson_case_results = collection.get(
        where={"resource_type": "lesson_case"},
        include=["documents", "metadatas"]
    )
    
    print(f"\n课例资源数量: {len(lesson_case_results['ids'])}")
    
    if lesson_case_results['ids']:
        print("\n前5个课例资源:")
        for i in range(min(5, len(lesson_case_results['ids']))):
            print(f"\n{i+1}. ID: {lesson_case_results['ids'][i]}")
            print(f"   文档: {lesson_case_results['documents'][i][:150]}...")
            print(f"   元数据: {lesson_case_results['metadatas'][i]}")
    else:
        print("向量数据库中没有课例资源")
else:
    print("向量数据库中没有集合")
