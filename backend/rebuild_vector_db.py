"""
重建向量数据库脚本
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.vector_database_builder import VectorDatabaseBuilder


def rebuild_vector_database():
    """重建向量数据库"""
    print("=" * 80)
    print("重建向量数据库")
    print("=" * 80)
    
    # 初始化构建器
    builder = VectorDatabaseBuilder(str(backend_path.parent / 'learning_resource'))
    
    # 打印当前数据库统计
    print("\n📊 当前数据库统计:")
    stats = builder.get_database_stats()
    print(f"   总记录数: {stats.get('total_count', 0)}")
    print(f"   类型统计: {stats.get('type_stats', {})}")
    print(f"   数据库路径: {stats.get('db_path', '')}")
    
    # 重建数据库
    print("\n🔄 开始重建向量数据库...")
    success = builder.build_vector_database(force_rebuild=True)
    
    if success:
        print("\n✅ 向量数据库重建成功！")
        
        # 打印新的数据库统计
        print("\n📊 新数据库统计:")
        stats = builder.get_database_stats()
        print(f"   总记录数: {stats.get('total_count', 0)}")
        print(f"   类型统计: {stats.get('type_stats', {})}")
    else:
        print("\n❌ 向量数据库重建失败！")
    
    print("\n" + "=" * 80)
    
    return success


if __name__ == "__main__":
    rebuild_vector_database()
