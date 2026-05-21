"""
查找余弦函数相关的复习课课件
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
print("查找余弦函数相关的复习课课件")
print("=" * 80)

cosine_review_coursewares = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    teaching_use = metadata.get('教学用途', '')
    
    # 检查是否包含"余弦"且是复习课
    if ('余弦' in filename or '余弦' in title) and '复习' in teaching_use:
        cosine_review_coursewares.append({
            '文件名': filename,
            '标题': title[:80],
            '教学用途': teaching_use,
        })

print(f"\n找到 {len(cosine_review_coursewares)} 个余弦函数相关的复习课课件:\n")
for i, cw in enumerate(cosine_review_coursewares[:10], 1):
    print(f"{i}. 文件名: {cw['文件名']}")
    print(f"   标题: {cw['标题']}")
    print(f"   教学用途: {cw['教学用途']}")
    print()

if len(cosine_review_coursewares) == 0:
    print("未找到任何余弦函数相关的复习课课件")
    print("\n检查是否有其他教学用途的余弦课件:")
    
    cosine_all = []
    for metadata in results['metadatas']:
        filename = metadata.get('文件名', '')
        title = metadata.get('标题', '')
        teaching_use = metadata.get('教学用途', '')
        
        if '余弦' in filename or '余弦' in title:
            cosine_all.append({
                '文件名': filename,
                '标题': title[:80],
                '教学用途': teaching_use,
            })
    
    print(f"\n总共找到 {len(cosine_all)} 个余弦相关课件，教学用途分布:")
    use_count = {}
    for cw in cosine_all:
        use = cw['教学用途']
        use_count[use] = use_count.get(use, 0) + 1
    
    for use, count in sorted(use_count.items(), key=lambda x: -x[1]):
        print(f"  {use}: {count}个")
