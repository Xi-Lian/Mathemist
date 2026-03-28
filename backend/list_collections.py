import chromadb
from chromadb.config import Settings

# 连接到向量数据库
client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/vector_db")

# 列出所有集合
collections = client.list_collections()

print(f"可用的集合:")
for i, collection in enumerate(collections):
    print(f"{i+1}. {collection.name}")