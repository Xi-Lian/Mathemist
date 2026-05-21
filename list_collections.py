import chromadb
import os

# 连接到ChromaDB
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend', 'chroma_db')
print(f"数据库路径: {db_path}")
client = chromadb.PersistentClient(path=db_path)

# 列出所有集合
collections = client.list_collections()

print('资源库中的集合:')
if not collections:
    print("没有找到任何集合")
else:
    for collection in collections:
        print(f'集合名称: {collection.name}')
