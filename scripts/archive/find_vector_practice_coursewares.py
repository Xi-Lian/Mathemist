"""
查找所有与"向量运算"相关的练习课课件
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
print("查找所有与'向量运算'相关的练习课课件")
print("=" * 80)

vector_practice_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    teaching_use = metadata.get('教学用途', '')
    content = metadata.get('内容', '')
    
    # 检查是否包含"向量"且是练习课
    if ('向量' in filename or '向量' in title or '向量' in content) and '练习' in teaching_use:
        vector_practice_coursewares.append({
            '文件名': filename,
            '标题': title,
            '教学用途': teaching_use,
            '内容': content[:50]
        })

print(f"\n找到 {len(vector_practice_coursewares)} 个向量相关的练习课课件:\n")
for i, cw in enumerate(vector_practice_coursewares[:10], 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['标题'][:80]}")
    print(f"   教学用途: {cw['教学用途']}")
    print(f"   内容预览: {cw['内容']}...")
    print()

if len(vector_practice_coursewares) == 0:
    print("未找到任何向量相关的练习课课件")
