"""
查找所有与"棱柱"相关的课件（放宽条件）
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
print("查找所有与'棱柱'相关的课件")
print("=" * 80)

all_prism_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    teaching_use = metadata.get('教学用途', '')
    content = metadata.get('内容', '')
    title = metadata.get('title', '')
    
    # 检查文件名、标题或内容中是否包含"棱柱"
    if '棱柱' in filename or '棱柱' in title or '棱柱' in content:
        all_prism_coursewares.append({
            '文件名': filename,
            '教学用途': teaching_use,
            '内容': content[:30],
            'title': title[:50]
        })

print(f"\n找到 {len(all_prism_coursewares)} 个与'棱柱'相关的课件:\n")
for i, cw in enumerate(all_prism_coursewares, 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['title']}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   内容预览: {cw['内容']}...")
    print()

if len(all_prism_coursewares) == 0:
    print("未找到任何与'棱柱'相关的课件")
