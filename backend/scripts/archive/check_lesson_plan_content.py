import chromadb
from chromadb.config import Settings
from pathlib import Path

# 获取ChromaDB客户端
db_path = Path(__file__).parent / 'chroma_db'
client = chromadb.PersistentClient(
    path=str(db_path),
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# 检查几何板块集合
try:
    collection = client.get_collection(name="math_resources_geometry")
    print("几何板块集合存在")
    
    # 获取前10个lesson_plan资源的文档内容
    results = collection.get(
        where={"resource_type": "lesson_plan"},
        include=["documents", "metadatas"],
        limit=10
    )
    
    print(f"获取到 {len(results['metadatas'])} 个lesson_plan资源")
    
    for i, (doc, meta) in enumerate(zip(results['documents'][:10], results['metadatas'][:10])):
        print(f"\n{'='*60}")
        print(f"资源 {i+1}:")
        print(f"标题: {meta.get('title', '无标题')}")
        print(f"文档长度: {len(doc) if doc else 0}")
        print(f"文档内容前500字符:")
        content = doc[:500] if doc else "无内容"
        print(content)
        print("...")

except Exception as e:
    print(f"查询失败: {str(e)}")
    import traceback
    traceback.print_exc()
