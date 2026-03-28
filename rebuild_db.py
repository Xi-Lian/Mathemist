#!/usr/bin/env python3
"""
重新构建向量数据库，确保所有资源都被正确索引
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.app.core.vector_database_builder import VectorDatabaseBuilder

def rebuild_database():
    """重新构建向量数据库"""
    # 创建VectorDatabaseBuilder实例
    builder = VectorDatabaseBuilder('learning_resource')
    
    # 强制重建数据库
    print("🔄 开始重建向量数据库...")
    success = builder.build_vector_database(force_rebuild=True)
    
    if success:
        print("✅ 向量数据库重建成功！")
        
        # 获取数据库统计信息
        stats = builder.get_database_stats()
        print("\n📊 向量数据库统计信息:")
        print(f"总记录数: {stats['total_count']}")
        print(f"数据库路径: {stats['db_path']}")
        
        print("\n📋 资源类型分布:")
        for resource_type, count in stats['type_stats'].items():
            print(f"  - {resource_type}: {count} 条")
    else:
        print("❌ 向量数据库重建失败！")

if __name__ == "__main__":
    rebuild_database()