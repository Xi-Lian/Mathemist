"""
检查第七章复数章末复习课件的详细元数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 查找第七章复数章末复习课件
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas', 'documents']
)

print("=" * 80)
print("查找第七章复数章末复习课件")
print("=" * 80)

for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    
    if '章末复习' in filename or '章末复习' in title:
        print(f"\n文件名: {filename}")
        print(f"标题: {title}")
        print(f"教学用途: {metadata.get('教学用途', '')}")
        print(f"源文件: {metadata.get('source_file', '')}")
        print(f"原文件云端链接: {metadata.get('原文件云端链接', '')}")
        print(f"云端链接: {metadata.get('云端链接', '')}")
        print(f"板块: {metadata.get('板块', '')}")
        print(f"知识点: {metadata.get('知识点', '')}")
        print(f"知识点标签: {metadata.get('知识点标签', '')}")
        print(f"resource_type: {metadata.get('resource_type', '')}")
        print()
        
        # 显示所有元数据字段
        print("所有元数据字段:")
        for key, value in metadata.items():
            if value and key not in ['内容', 'document']:
                print(f"  {key}: {value}")
        break
