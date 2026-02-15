import chromadb
from pathlib import Path

# 连接到向量数据库
db_path = Path("d:/Git_Repository/Mathemist/backend/app/data/chroma_db")
client = chromadb.PersistentClient(path=str(db_path))

# 获取集合
collection = client.get_collection(name="math_resources")

# 查询课例资源
lesson_case_results = collection.get(
    where={"resource_type": "lesson_case"},
    include=["documents", "metadatas"]
)

print(f"向量数据库中的课例资源数量: {len(lesson_case_results['ids'])}")

if lesson_case_results['ids']:
    print("\n前10个课例资源的描述:")
    for i in range(min(10, len(lesson_case_results['ids']))):
        print(f"\n{i+1}. ID: {lesson_case_results['ids'][i]}")
        print(f"   文档: {lesson_case_results['documents'][i]}")
        print(f"   元数据: {lesson_case_results['metadatas'][i]}")
else:
    print("向量数据库中没有课例资源")
