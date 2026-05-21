"""
检查复数章末复习课件的完整元数据和路径
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 查找所有复数相关的课件
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas']
)

print("=" * 80)
print("查找所有复数相关的课件及其路径")
print("=" * 80)

complex_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    
    if '复数' in filename or '复数' in title or '第七章' in filename:
        source_file = metadata.get('source_file', '')
        cloud_url = metadata.get('云端链接', '')
        original_file_url = metadata.get('原文件云端链接', '')
        
        complex_coursewares.append({
            '文件名': filename,
            '标题': title[:60],
            '教学用途': metadata.get('教学用途', ''),
            'source_file': source_file,
            '云端链接': cloud_url[:100] if cloud_url else '无',
            '原文件云端链接': original_file_url[:100] if original_file_url else '无',
        })

# 按文件名排序
complex_coursewares.sort(key=lambda x: x['文件名'])

print(f"\n找到 {len(complex_coursewares)} 个复数相关的课件:\n")
for i, cw in enumerate(complex_coursewares, 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['标题']}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   source_file: {cw['source_file']}")
    print(f"   云端链接: {cw['云端链接']}")
    print(f"   原文件云端链接: {cw['原文件云端链接']}")
    print()
