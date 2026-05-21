import chromadb
from app.config.resource_type_config import get_db_type

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 测试资源类型映射
resource_types = ['课件', 'PPT', '教学设计', '习题']
print("测试资源类型映射:")
for rt in resource_types:
    db_type = get_db_type(rt)
    print(f"  {rt} -> {db_type}")

print("\n执行向量检索测试:")
# 模拟检索
query_text = "组合数 练习课 课件"

# 按课件类型检索
results = prob_coll.query(
    query_texts=[query_text],
    n_results=20,
    where={"resource_type": "courseware"},
    include=["documents", "metadatas", "distances"]
)

print(f"\n找到 {len(results['documents'][0])} 条课件资源")
print("前5条结果的距离:")
for i in range(min(5, len(results['distances'][0]))):
    dist = results['distances'][0][i]
    title = results['metadatas'][0][i].get('title', '未知')
    teaching_use = results['metadatas'][0][i].get('教学用途', '未知')
    print(f"  {i+1}. distance={dist:.4f}, 标题={title[:30]}, 教学用途={teaching_use}")

# 检查是否有练习课课件
print("\n检查练习课课件的距离:")
for i, meta in enumerate(results['metadatas'][0]):
    if meta.get('教学用途') == '练习课课件':
        dist = results['distances'][0][i]
        title = meta.get('title', '未知')
        print(f"  ✅ 练习课课件: distance={dist:.4f}, 标题={title}")
