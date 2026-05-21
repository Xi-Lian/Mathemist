"""
查找余弦函数相关的练习课课件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_function')

# 获取所有课件资源
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas']
)

print("=" * 80)
print("查找余弦函数相关的练习课/习题课课件")
print("=" * 80)

cosine_practice_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    teaching_use = metadata.get('教学用途', '')
    
    # 检查是否包含"余弦"且是练习课或习题课
    if ('余弦' in filename or '余弦' in title) and ('练习' in teaching_use or '习题' in teaching_use):
        cosine_practice_coursewares.append({
            '文件名': filename,
            '标题': title[:80],
            '教学用途': teaching_use,
        })

print(f"\n找到 {len(cosine_practice_coursewares)} 个余弦函数相关的练习课/习题课课件:\n")
for i, cw in enumerate(cosine_practice_coursewares[:10], 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['标题']}")
    print(f"   教学用途: {cw['教学用途']}")
    print()

if len(cosine_practice_coursewares) == 0:
    print("未找到任何余弦函数相关的练习课/习题课课件")
    print("\n结论：数据库中既没有余弦函数的复习课，也没有练习课/习题课课件")
    print("V43.0降级策略将无法生效，因为没有可降级的目标资源")
