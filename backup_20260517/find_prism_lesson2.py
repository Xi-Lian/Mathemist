"""
查找所有文件名或内容中包含"课时2"和"棱柱"的练习课课件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 获取所有课件资源
results = coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])

print("=" * 80)
print("查找所有'课时2'相关的练习课课件")
print("=" * 80)

practice_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    teaching_use = metadata.get('教学用途', '')
    content = metadata.get('内容', '')
    title = metadata.get('title', '')
    
    # 检查是否是8.1课时2且是练习课
    if '8.1' in filename and '课时2' in (filename + content + title) and '练习' in teaching_use:
        practice_coursewares.append({
            '文件名': filename,
            '教学用途': teaching_use,
            '内容': content,
            'title': title
        })

print(f"\n找到 {len(practice_coursewares)} 个8.1课时2的练习课课件:\n")
for i, cw in enumerate(practice_coursewares, 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['title']}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   内容: {cw['内容']}")
    print(f"   文件名包含'棱柱': {'棱柱' in cw['文件名']}")
    print(f"   标题包含'棱柱': {'棱柱' in cw['title']}")
    print(f"   内容包含'棱柱': {'棱柱' in cw['内容']}")
    print()

if len(practice_coursewares) == 0:
    print("未找到任何8.1课时2的练习课课件")
