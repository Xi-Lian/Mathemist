import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

# 连接到向量数据库
db_path = Path("d:/Git_Repository/Mathemist/backend/app/data/chroma_db")
client = chromadb.PersistentClient(path=str(db_path))

# 获取集合
collection = client.get_collection(name="math_resources")

# 加载embedding模型
model = SentenceTransformer(r"C:\Users\15137\.cache\huggingface\hub\models--sentence-transformers--paraphrase-multilingual-MiniLM-L12-v2\snapshots\e8f8c211226b894fcb81acc59f3b34ba3efd5f42")

# 测试查询
query = "查找指数函数的课件和课例"
query_embedding = model.encode([query], normalize_embeddings=True).tolist()

# 测试1：不指定资源类型
print("=" * 80)
print("测试1：不指定资源类型")
print("=" * 80)
results1 = collection.query(
    query_embeddings=query_embedding,
    n_results=10,
    include=["documents", "metadatas", "distances"]
)

print(f"\n检索到的资源数量: {len(results1['ids'][0])}")
for i in range(len(results1['ids'][0])):
    resource_type = results1['metadatas'][0][i].get('resource_type', 'unknown')
    distance = results1['distances'][0][i]
    print(f"{i+1}. 类型: {resource_type}, 距离: {distance:.4f}, 文档: {results1['documents'][0][i][:80]}...")

# 测试2：指定资源类型为['课件', '课例']
print("\n" + "=" * 80)
print("测试2：指定资源类型为['课件', '课例']")
print("=" * 80)

# ChromaDB不支持where和query_embeddings一起使用，所以我们需要在客户端过滤
# 先查询所有资源，然后过滤
results2 = collection.query(
    query_embeddings=query_embedding,
    n_results=50,
    include=["documents", "metadatas", "distances"]
)

# 过滤资源类型
filtered_results = []
for i in range(len(results2['ids'][0])):
    resource_type = results2['metadatas'][0][i].get('resource_type', 'unknown')
    if resource_type in ['courseware', 'lesson_case']:
        filtered_results.append(i)

print(f"\n过滤后的资源数量: {len(filtered_results)}")
for i in filtered_results[:10]:
    resource_type = results2['metadatas'][0][i].get('resource_type', 'unknown')
    distance = results2['distances'][0][i]
    print(f"{i+1}. 类型: {resource_type}, 距离: {distance:.4f}, 文档: {results2['documents'][0][i][:80]}...")

# 测试3：只指定资源类型为['课例']
print("\n" + "=" * 80)
print("测试3：只指定资源类型为['课例']")
print("=" * 80)

# 过滤课例资源
filtered_lesson_cases = []
for i in range(len(results2['ids'][0])):
    resource_type = results2['metadatas'][0][i].get('resource_type', 'unknown')
    if resource_type == 'lesson_case':
        filtered_lesson_cases.append(i)

print(f"\n过滤后的课例资源数量: {len(filtered_lesson_cases)}")
for i in filtered_lesson_cases[:10]:
    resource_type = results2['metadatas'][0][i].get('resource_type', 'unknown')
    distance = results2['distances'][0][i]
    print(f"{i+1}. 类型: {resource_type}, 距离: {distance:.4f}, 文档: {results2['documents'][0][i][:80]}...")
