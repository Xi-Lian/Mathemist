import chromadb

# 连接数据库
client = chromadb.PersistentClient(path='./chroma_db')

# 列出所有集合
collections = client.list_collections()
print("=== 数据库集合 ===")
for coll in collections:
    print(f"- {coll.name}: {coll.count()} 条记录")

# 检查函数板块
print("\n=== 函数板块内容 ===")
coll = client.get_collection('math_resources_function')
data = coll.peek(limit=3)

print("\nDocuments (前3条):")
for i, doc in enumerate(data['documents']):
    print(f"{i+1}. {doc[:150]}...")

print("\nMetadatas (前3条):")
for i, meta in enumerate(data['metadatas']):
    print(f"{i+1}. resource_type={meta.get('resource_type')}, board={meta.get('board')}")
    if 'analysis_json' in meta:
        print(f"   analysis_json exists: {len(meta['analysis_json']) > 0}")

# 测试查询
print("\n=== 测试查询 '三角恒等变换' ===")
results = coll.query(
    query_texts=["三角恒等变换"],
    n_results=5,
    where={"resource_type": "exercise"}
)
print(f"查询返回 {len(results['documents'][0])} 条结果")
if results['documents'][0]:
    for i, (doc, meta) in enumerate(zip(results['documents'][0], results['metadatas'][0])):
        print(f"{i+1}. {doc[:100]}...")
        print(f"   resource_type={meta.get('resource_type')}, analysis_json存在={len(meta.get('analysis_json',''))>0}")

# 检查resource_type字段的值分布
print("\n=== 检查resource_type字段 ===")
import json
# 获取所有resource_type
all_metas = coll.get()['metadatas']
type_counts = {}
for meta in all_metas:
    rt = meta.get('resource_type', 'unknown')
    type_counts[rt] = type_counts.get(rt, 0) + 1
print(f"resource_type分布: {type_counts}")

# 直接测试简化检索
print("\n=== 直接测试简化检索 ===")
import sys
sys.path.insert(0, '.')
from app.core.retrieval.simple_exercise_retrieval import simple_exercise_retrieval

results = simple_exercise_retrieval(
    query="三角恒等变换 习题",
    core_theme="三角恒等变换",
    vector_db=client,
    n_results=10,
    resource_types=["exercise"]
)
print(f"简化检索返回 {len(results)} 条结果")
if results:
    for i, r in enumerate(results[:3]):
        print(f"{i+1}. score={r['score']:.4f}, distance={r['distance']:.4f}")
        print(f"   document: {r['document'][:80]}...")
