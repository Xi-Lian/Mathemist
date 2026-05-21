#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

from app.core.vector_database_builder import VectorDatabaseBuilder

print("=" * 60)
print("开始重建向量数据库（force_rebuild=True）")
print("=" * 60)

try:
    builder = VectorDatabaseBuilder('learning_resource')
    success = builder.build_vector_database(force_rebuild=True)

    if success:
        print("\n✅ 向量数据库重建成功！")
        stats = builder.get_database_stats()
        print(f"数据库路径: {stats.get('db_path', '未知')}")
        print(f"记录总数: {stats.get('total_count', 0)}")
        if stats.get('type_stats'):
            print("\n资源类型统计:")
            for resource_type, count in stats['type_stats'].items():
                print(f"  - {resource_type}: {count}条")
        if stats.get('board_stats'):
            print("\n板块统计:")
            for board, count in stats['board_stats'].items():
                print(f"  - {board}: {count}条")
    else:
        print("\n❌ 向量数据库重建失败")

except Exception as e:
    print(f"\n❌ 重建过程发生错误: {e}")
    import traceback
    traceback.print_exc()
