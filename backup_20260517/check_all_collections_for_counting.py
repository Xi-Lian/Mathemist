"""
检查所有ChromaDB集合中的计数原理相关课件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()

collections = client.list_collections()

print("=" * 80)
print("检查所有集合中的计数原理相关课件")
print("=" * 80)

for col in collections:
    print(f"\n集合: {col.name} (文档数: {col.count()})")
    
    # 获取所有课件资源
    try:
        results = col.get(
            where={'resource_type': 'courseware'},
            include=['metadatas'],
            limit=1000
        )
        
        counting_count = 0
        for metadata in results['metadatas']:
            filename = metadata.get('文件名', '')
            title = metadata.get('标题', '')
            
            if ('分步' in filename or '分步' in title or 
                '计数' in filename or '计数' in title or
                '排列' in filename or '排列' in title or
                '组合' in filename or '组合' in title):
                counting_count += 1
                teaching_use = metadata.get('教学用途', '')
                print(f"  - {filename[:60]} (用途: {teaching_use})")
        
        if counting_count > 0:
            print(f"  总计: {counting_count} 个相关课件")
        else:
            print(f"  未找到相关课件")
            
    except Exception as e:
        print(f"  查询失败: {e}")
