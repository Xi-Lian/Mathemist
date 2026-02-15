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

# 查找包含"指数函数"的课例
print("\n包含'指数函数'的课例资源:")
for i in range(len(lesson_case_results['ids'])):
    doc = lesson_case_results['documents'][i]
    if '指数函数' in doc:
        print(f"\n{i+1}. ID: {lesson_case_results['ids'][i]}")
        print(f"   文档: {doc}")
        print(f"   元数据: {lesson_case_results['metadatas'][i]}")
