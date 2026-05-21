"""
直接搜索包含'章末复习'的课件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 获取所有课件
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas']
)

print("=" * 80)
print("搜索包含'章末复习'的课件")
print("=" * 80)

found = False
for i, metadata in enumerate(results['metadatas']):
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    
    if '章末复习' in filename or '章末复习' in title:
        found = True
        print(f"\n找到第 {i+1} 条记录:")
        print(f"  ID: {results['ids'][i]}")
        print(f"  文件名: {filename}")
        print(f"  标题: {title}")
        print(f"  教学用途: {metadata.get('教学用途', '')}")
        cloud_url = metadata.get('云端链接', '')
        print(f"  云端链接: {cloud_url[:120] if cloud_url else '无'}")

if not found:
    print("\n[完成] 数据库中没有任何包含'章末复习'的课件记录")
else:
    print(f"\n总共找到 {sum(1 for m in results['metadatas'] if '章末复习' in m.get('文件名', '') or '章末复习' in m.get('title', ''))} 条记录")
