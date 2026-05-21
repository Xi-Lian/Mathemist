"""
检查第七章复数课件的元数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 查找第七章复数相关的课件
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas', 'documents']
)

print("=" * 80)
print("查找第七章复数相关的课件")
print("=" * 80)

complex_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    teaching_use = metadata.get('教学用途', '')
    source_file = metadata.get('source_file', '') or metadata.get('原文件云端链接', '')
    
    # 检查是否包含"复数"或"第七章"
    if ('复数' in filename or '复数' in title or '第七章' in filename or '第七章' in title):
        complex_coursewares.append({
            '文件名': filename,
            '标题': title,
            '教学用途': teaching_use,
            '源文件': source_file[:100] if source_file else '无',
        })

print(f"\n找到 {len(complex_coursewares)} 个复数相关的课件:\n")
for i, cw in enumerate(complex_coursewares[:10], 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['标题'][:80]}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   源文件: {cw['源文件']}")
    print()

if len(complex_coursewares) == 0:
    print("未找到任何复数相关的课件")
