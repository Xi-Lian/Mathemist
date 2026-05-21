#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 确保 backend 在路径中
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    print("=" * 60)
    print("开始重新构建向量数据库（强制同步 AnalysisLoader 数据）")
    print("=" * 60)
    
    try:
        # 创建构建器，指向根目录下的 learning_resource
        builder = VectorDatabaseBuilder('learning_resource')
        
        print("\n正在强制重建向量数据库...")
        success = builder.build_vector_database(force_rebuild=True)
        
        if success:
            print("\n[SUCCESS] 向量数据库构建成功！")
            stats = builder.get_database_stats()
            print(f"数据库路径: {stats.get('db_path', '未知')}")
            print(f"记录总数: {stats.get('total_count', 0)}")
            if stats.get('type_stats'):
                print("\n资源类型统计:")
                for resource_type, count in stats['type_stats'].items():
                    print(f"  - {resource_type}: {count}条")
        else:
            print("\n[ERROR] 向量数据库构建失败")
            
    except Exception as e:
        print(f"\n[ERROR] 构建过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
