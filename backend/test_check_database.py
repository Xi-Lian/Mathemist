"""
检查数据库中的4.2指数函数教案
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.vector_db_builder import VectorDBBuilder


def check_database_contents():
    """检查数据库中的内容"""
    print("=" * 80)
    print("检查向量数据库中的内容")
    print("=" * 80)
    
    builder = VectorDBBuilder()
    
    if not builder.check_database_exists():
        print("❌ 数据库不存在！")
        return
    
    print("✅ 数据库存在")
    
    client = builder.get_chroma_client()
    collection = client.get_collection(name=builder.COLLECTION_NAME)
    
    print(f"\n📊 集合信息:")
    print(f"   集合名称: {collection.name}")
    print(f"   文档数量: {collection.count()}")
    
    all_docs = collection.get(include=["metadatas", "documents"])
    
    print(f"\n📋 总文档数: {len(all_docs['ids'])}")
    
    lesson_plans = []
    for i, metadata in enumerate(all_docs["metadatas"]):
        if metadata.get("resource_type") == "lesson_plan":
            lesson_plans.append({
                "id": all_docs["ids"][i],
                "metadata": metadata,
                "document": all_docs["documents"][i]
            })
    
    print(f"\n📚 教案资源数量: {len(lesson_plans)}")
    
    print(f"\n🔍 查找包含'4.2'或'指数函数'的教案:")
    found_42 = []
    for lp in lesson_plans:
        metadata = lp["metadata"]
        source_file = metadata.get("source_file", "")
        title = metadata.get("title", "")
        
        if "4.2" in source_file or "指数函数" in title or "指数函数" in source_file:
            found_42.append(lp)
    
    print(f"✅ 找到 {len(found_42)} 个4.2指数函数相关教案")
    
    if found_42:
        print(f"\n📄 前10个4.2指数函数教案:")
        for i, lp in enumerate(found_42[:10]):
            metadata = lp["metadata"]
            filename = Path(metadata.get("source_file", "")).name
            title = metadata.get("title", "未知")
            print(f"\n{i+1:2d}. {filename}")
            print(f"      标题: {title}")
            print(f"      资源类型: {metadata.get('resource_type')}")
            print(f"      章节: {metadata.get('章节', '未知')}")
            print(f"      知识点标签: {metadata.get('知识点标签', '未知')}")
    
    print(f"\n" + "=" * 80)
    print(f"📋 所有教案的文件名（前30个）:")
    print("=" * 80)
    for i, lp in enumerate(lesson_plans[:30]):
        filename = Path(lp["metadata"].get("source_file", "")).name
        print(f"{i+1:2d}. {filename}")
    
    print("\n" + "=" * 80)
    print("检查完成！")
    print("=" * 80)


if __name__ == "__main__":
    check_database_contents()
