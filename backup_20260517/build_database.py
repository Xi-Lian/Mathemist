#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    print("=" * 60)
    print("开始构建向量数据库")
    print("=" * 60)
    
    try:
        # 创建构建器
        builder = VectorDatabaseBuilder('learning_resource')
        
        # 检查数据库是否已存在
        if builder.check_database_exists():
            print("\n检测到向量数据库已存在")
            print("是否强制重建？(y/n)")
            # 自动选择否，避免意外删除数据
            choice = 'n'
            print(f"选择: {choice}")
            
            if choice.lower() == 'y':
                print("正在重建向量数据库...")
                success = builder.build_vector_database(force_rebuild=True)
            else:
                print("跳过构建，使用现有数据库")
                success = True
        else:
            print("\n向量数据库不存在，开始构建...")
            success = builder.build_vector_database(force_rebuild=False)
        
        if success:
            print("\n✅ 向量数据库构建成功！")
            stats = builder.get_database_stats()
            print(f"数据库路径: {stats.get('db_path', '未知')}")
            print(f"记录总数: {stats.get('total_count', 0)}")
            if stats.get('type_stats'):
                print("\n资源类型统计:")
                for resource_type, count in stats['type_stats'].items():
                    print(f"  - {resource_type}: {count}条")
        else:
            print("\n❌ 向量数据库构建失败")
            
    except Exception as e:
        print(f"\n❌ 构建过程发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()