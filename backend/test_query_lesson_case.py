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
query = "查找指数函数课例"

print(f"查询: {query}")
print(f"{'=' * 80}")

query_embedding = model.encode([query], normalize_embeddings=True).tolist()

# 查询所有资源
results = collection.query(
    query_embeddings=query_embedding,
    n_results=200,
    include=["documents", "metadatas", "distances"]
)

# 过滤课例资源
lesson_cases = []
for i in range(len(results['ids'][0])):
    resource_type = results['metadatas'][0][i].get('resource_type', 'unknown')
    if resource_type == 'lesson_case':
        lesson_cases.append(i)

print(f"课例资源数量: {len(lesson_cases)}")

if lesson_cases:
    print(f"课例资源在前200个结果中的位置和距离:")
    for i in lesson_cases[:5]:
        distance = results['distances'][0][i]
        doc = results['documents'][0][i]
        print(f"  {i+1}. 距离: {distance:.4f}, 文档: {doc[:80]}...")
