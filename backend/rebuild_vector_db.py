import os
from app.core.vector_database_builder import VectorDatabaseBuilder

# 获取learning_resource路径
current_dir = os.path.dirname(os.path.abspath(__file__))
learning_resource_path = os.path.join(current_dir, '..', 'learning_resource')

print(f"Learning resource path: {learning_resource_path}")

# 初始化构建器
builder = VectorDatabaseBuilder(learning_resource_path)

# 检查数据库状态
print('向量数据库状态:', '存在' if builder.check_database_exists() else '不存在')

# 强制重建向量数据库
print('正在强制重建向量数据库...')
builder.build_vector_database(force_rebuild=True)

# 检查重建后的状态
print('重建完成，向量数据库状态:', '存在' if builder.check_database_exists() else '不存在')

# 尝试获取资源数量
if builder.check_database_exists():
    try:
        client = builder.get_chroma_client()
        collection = client.get_collection(name="math_resources")
        count = collection.count()
        print('资源数量:', count)
    except Exception as e:
        print('获取资源数量失败:', str(e))
