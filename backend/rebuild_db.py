"""
重新构建向量数据库
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.vector_database_builder import VectorDatabaseBuilder


print("=" * 80)
print("重新构建向量数据库")
print("=" * 80)

# 获取正确的learning_resource路径
backend_dir = Path(__file__).parent
project_root = backend_dir.parent
learning_resource_path = project_root / 'learning_resource'

print(f"\n📂 Learning Resource路径: {learning_resource_path}")

builder = VectorDatabaseBuilder(str(learning_resource_path))

print(f"\n🔨 开始构建新数据库（强制重建）...")
success = builder.build_vector_database(force_rebuild=True)

if success:
    print("\n✅ 数据库构建成功！")
    
    # 验证一下
    client = builder.get_chroma_client()
    collection = client.get_collection(name=builder.COLLECTION_NAME)
    print(f"\n📊 集合信息:")
    print(f"   文档数量: {collection.count()}")
else:
    print("\n❌ 数据库构建失败！")
    sys.exit(1)

print("\n" + "=" * 80)
print("完成！")
print("=" * 80)
