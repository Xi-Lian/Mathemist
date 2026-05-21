#!/usr/bin/env python
"""
V45.1 修复课例视频标题问题
只重新导入课例视频资源，不重建整个数据库
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

def fix_lesson_case_titles():
    """修复课例视频标题问题"""
    print("=" * 80)
    print("V45.1 修复课例视频标题")
    print("=" * 80)
    
    # 1. 删除旧的课例视频数据
    print("\n步骤1: 删除向量数据库中的旧课例视频数据...")
    vdb = VectorDatabaseBuilder('learning_resource')
    client = vdb.get_chroma_client()
    
    collections = client.list_collections()
    deleted_count = 0
    
    for col in collections:
        try:
            # 查找课例视频资源
            results = col.get(
                where={'resource_type': 'lesson_case'},
                include=['metadatas']
            )
            
            if results['ids']:
                count = len(results['ids'])
                print(f"  集合 {col.name}: 找到 {count} 个课例视频，正在删除...")
                col.delete(ids=results['ids'])
                deleted_count += count
        except Exception as e:
            print(f"  集合 {col.name}: 删除失败 - {e}")
    
    print(f"\n[OK] 共删除 {deleted_count} 个旧课例视频记录")
    
    # 2. 重新构建向量数据库（只导入课例视频）
    print("\n步骤2: 重新构建向量数据库（使用新的标题生成逻辑）...")
    print("  注意：这将重新解析所有资源表，但只会更新课例视频部分")
    
    success = vdb.build_vector_database(force_rebuild=False, batch_size=50)
    
    if success:
        print("\n[OK] 向量数据库重建成功！")
    else:
        print("\n[ERROR] 向量数据库重建失败")
    
    return success

if __name__ == "__main__":
    try:
        success = fix_lesson_case_titles()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
