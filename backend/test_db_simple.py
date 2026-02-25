"""
简单检查数据库
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder()

if not builder.check_database_exists():
    print("❌ 数据库不存在！")
    sys.exit(1)

print("✅ 数据库存在")

client = builder.get_chroma_client()
collection = client.get_collection(name=builder.COLLECTION_NAME)

print("\n📊 集合信息:")
print(f"   集合名称: {collection.name}")
print(f"   文档数量: {collection.count()}")

all_docs = collection.get(include=["metadatas", "documents"])

print("\n📋 总文档数:", len(all_docs['ids']))

lesson_plans = []
for i, metadata in enumerate(all_docs["metadatas"]):
    if metadata.get("resource_type") == "lesson_plan":
        lesson_plans.append(metadata)

print("\n📚 教案资源数量:", len(lesson_plans))

print("\n🔍 查找4.2指数函数教案:")
found = []
for lp in lesson_plans:
    source = lp.get("source_file", "")
    title = lp.get("title", "")
    if "4.2" in source or "指数函数" in title or "指数函数" in source:
        found.append(lp)

print("✅ 找到", len(found), "个相关教案")

if found:
    print("\n📄 前10个:")
    for i, lp in enumerate(found[:10]):
        filename = Path(lp.get("source_file", "")).name
        print(f"{i+1}. {filename}")

print("\n📋 所有教案文件名（前30）:")
for i, lp in enumerate(lesson_plans[:30]):
    filename = Path(lp.get("source_file", "")).name
    print(f"{i+1}. {filename}")
