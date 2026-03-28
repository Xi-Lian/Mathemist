import chromadb

# 连接到ChromaDB
client = chromadb.PersistentClient(path='backend/data/chroma_db')

# 列出所有集合
collections = client.list_collections()

print('资源库中的集合:')
for collection in collections:
    print(f'集合名称: {collection.name}')
