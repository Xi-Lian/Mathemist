#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    print("=" * 60)
    print("强制重建向量数据库")
    print("=" * 60)
    
    try:
        builder = VectorDatabaseBuilder('learning_resource')
        
        print("正在构建向量数据库...")
        print("注意：习题资源将使用通义千问进行分析增强")
        print("这可能需要较长时间，请耐心等待...")
        print()
        
        success = builder.build_vector_database(force_rebuild=True)
        
        if success:
            print()
            print("数据库构建成功")
            print("=" * 60)
            stats = builder.get_database_stats()
            print("数据库路径: %s" % stats.get('db_path', '未知'))
            print("记录总数: %d" % stats.get('total_count', 0))
            if stats.get('type_stats'):
                print()
                print("资源类型统计:")
                for resource_type, count in stats['type_stats'].items():
                    print("  - %s: %d条" % (resource_type, count))
        else:
            print()
            print("数据库构建失败")
            
    except Exception as e:
        print()
        print("构建过程发生错误: %s" % e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()