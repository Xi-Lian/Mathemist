"""
详细查看4.2指数函数文件在数据库中的情况
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.vector_database_builder import VectorDatabaseBuilder


def test_42_in_db():
    """检查4.2指数函数文件在数据库中的情况"""
    print("=" * 80)
    print("检查4.2指数函数文件在数据库中的情况")
    print("=" * 80)
    
    # 获取正确的learning_resource路径
    backend_dir = Path(__file__).parent
    project_root = backend_dir.parent
    learning_resource_path = project_root / 'learning_resource'
    
    print(f"\n📂 Learning Resource路径: {learning_resource_path}")
    
    builder = VectorDatabaseBuilder(str(learning_resource_path))
    
    print(f"\n🔍 连接到数据库...")
    client = builder.get_chroma_client()
    collection = client.get_collection(name=builder.COLLECTION_NAME)
    
    print(f"\n📊 数据库总记录数: {collection.count()}")
    
    print(f"\n🔍 查找所有包含4.2指数函数的记录...")
    results = collection.get(include=['metadatas', 'documents'])
    
    count_42 = 0
    real_42 = []
    
    for i, metadata in enumerate(results['metadatas']):
        source_file = metadata.get('source_file', '')
        if '4.2' in source_file and '指数函数' in source_file and '4.4' not in source_file:
            count_42 += 1
            real_42.append({
                'index': i,
                'metadata': metadata,
                'document': results['documents'][i] if i < len(results['documents']) else ''
            })
            print(f"\n{'=' * 80}")
            print(f"✅ 找到真正的4.2指数函数 #{count_42}:")
            print(f"源文件: {source_file}")
            print(f"资源类型: {metadata.get('resource_type', 'N/A')}")
            print(f"标题: {metadata.get('title', 'N/A')}")
            if i < len(results['documents']):
                doc_preview = results['documents'][i][:150] if results['documents'][i] else ''
                print(f"文档预览: {doc_preview}...")
    
    print(f"\n✅ 真正的4.2指数函数文件在数据库中: {count_42} 条")
    
    if count_42 == 0:
        print(f"\n❌ 数据库中没有真正的4.2指数函数文件！")
        print(f"\n📋 让我们检查一下数据库中的所有教案资源...")
        
        lesson_plan_count = 0
        for metadata in results['metadatas']:
            if metadata.get('resource_type') == 'lesson_plan':
                lesson_plan_count += 1
                source_file = metadata.get('source_file', '')
                if lesson_plan_count <= 20:
                    print(f"  {lesson_plan_count}. {source_file}")
        
        print(f"\n📊 数据库中总教案数: {lesson_plan_count}")


if __name__ == "__main__":
    test_42_in_db()
