"""
查找所有包含"棱柱"且是"练习课"的课件
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
print("查找所有包含'棱柱'且是'练习课'的课件")
print("=" * 80)

matching_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    teaching_use = metadata.get('教学用途', '')
    
    # 检查是否包含"棱柱"且是练习课
    if '棱柱' in filename and '练习' in teaching_use:
        matching_coursewares.append({
            '文件名': filename,
            '教学用途': teaching_use,
            '内容': metadata.get('内容', ''),
            'title': metadata.get('title', '')
        })

print(f"\n找到 {len(matching_coursewares)} 个符合条件的课件:\n")
for i, cw in enumerate(matching_coursewares, 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   内容: {cw['内容'][:50]}...")
    print()

if len(matching_coursewares) == 0:
    print("未找到任何符合条件的课件")
    print("\n尝试放宽条件，查找所有练习课课件:")
    
    practice_coursewares = []
    for metadata in results['metadatas']:
        filename = metadata.get('文件名', '')
        teaching_use = metadata.get('教学用途', '')
        
        if '练习' in teaching_use and ('8.1' in filename or '基本立体' in filename):
            practice_coursewares.append({
                '文件名': filename,
                '教学用途': teaching_use,
                '内容': metadata.get('内容', ''),
            })
    
    print(f"\n找到 {len(practice_coursewares)} 个8.1相关的练习课课件:\n")
    for i, cw in enumerate(practice_coursewares[:10], 1):
        print(f"{i}. 文件名: {cw['文件名']}")
        print(f"   教学用途: {cw['教学用途']}")
        print(f"   内容: {cw['内容'][:50]}...")
        print()
