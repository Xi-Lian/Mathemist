import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')

# 获取所有集合
collections = client.list_collections()

print("向量数据库中的集合:")
for coll in collections:
    print(f"  - {coll.name}")
    
    # 获取集合中的资源类型统计
    try:
        all_results = coll.get(include=['metadatas'])
        if all_results['metadatas']:
            resource_types = {}
            for meta in all_results['metadatas']:
                rt = meta.get('resource_type', 'unknown')
                resource_types[rt] = resource_types.get(rt, 0) + 1
            
            print(f"    资源类型分布:")
            for rt, count in resource_types.items():
                print(f"      - {rt}: {count}")
    except Exception as e:
        print(f"    获取元数据失败: {e}")
