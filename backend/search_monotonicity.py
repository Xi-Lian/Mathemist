import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import chromadb
from chromadb.config import Settings

# 初始化ChromaDB
client = chromadb.Client(Settings(
    persist_directory="./chroma_db",
    anonymized_telemetry=False
))

# 获取集合 - 使用正确的集合名称
collection = client.get_or_create_collection(name="math_resources")

# 测试查询
query = "函数单调性的证明题"

# 执行向量检索，获取足够多的结果
print("执行向量检索，n_results=500")
results = collection.query(
    query_texts=[query],
    n_results=500,
    where={"resource_type": "exercise"},
    include=["documents", "metadatas", "distances"]
)

# 分析结果
print(f"\n检索到 {len(results['metadatas'][0])} 个结果")

# 检查是否包含单调性和证明相关关键词的习题
print("\n检查结果中是否包含单调性和证明相关关键词的习题:")
print("-" * 60)

monotonicity_proof_found = False
for i, (doc, meta, distance) in enumerate(zip(
    results['documents'][0],
    results['metadatas'][0],
    results['distances'][0]
)):
    # 检查文档内容是否包含单调性相关关键词
    if '单调性' in doc or '单调' in doc:
        print(f"\n找到包含单调性的习题 #{i+1}:")
        print(f"距离: {distance:.4f}")
        print(f"来源: {meta.get('source_file', '未知')}")
        print(f"题目类型: {meta.get('题目类型', '未知')}")
        print(f"知识点标签: {meta.get('知识点标签', '未知')}")
        print(f"题干: {doc[:100]}...")
        monotonicity_proof_found = True

if not monotonicity_proof_found:
    print("未找到包含单调性的习题")

# 打印前10个结果的信息
print("\n前10个结果的信息:")
print("-" * 60)

for i, (doc, meta, distance) in enumerate(zip(
    results['documents'][0][:10],
    results['metadatas'][0][:10],
    results['distances'][0][:10]
)):
    print(f"\n结果 #{i+1}:")
    print(f"距离: {distance:.4f}")
    print(f"来源: {meta.get('source_file', '未知')}")
    print(f"题目类型: {meta.get('题目类型', '未知')}")
    print(f"知识点标签: {meta.get('知识点标签', '未知')}")
    print(f"题干: {doc[:100]}...")
