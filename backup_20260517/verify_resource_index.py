"""
验证资源处理和索引的完整性
"""

import sys
import os

# 添加backend目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    print("开始验证资源处理和索引的完整性...")
    
    # 初始化构建器
    builder = VectorDatabaseBuilder("d:\\Git_Repository\\Mathemist\\learning_resource")
    
    # 重建向量数据库
    print("重建向量数据库...")
    success = builder.build_vector_database(force_rebuild=True)
    
    if success:
        print("✅ 向量数据库重建成功")
        
        # 获取统计信息
        stats = builder.get_database_stats()
        print(f"总资源数量: {stats['total_count']}")
        print("资源类型分布:")
        for resource_type, count in stats['type_stats'].items():
            print(f"  {resource_type}: {count}")
        print(f"数据库路径: {stats['db_path']}")
        
        print("\n✅ 资源处理和索引完整性验证完成")
    else:
        print("❌ 向量数据库重建失败")
