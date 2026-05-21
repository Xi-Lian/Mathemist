"""
检查分步乘法计数原理相关的课件
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 获取所有课件资源
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas']
)

print("=" * 80)
print("查找分步乘法计数原理相关的课件")
print("=" * 80)

counting_principle_all = []
for metadata in results['metadatas']:
    filename = metadata.get('文件名', '')
    title = metadata.get('标题', '')
    teaching_use = metadata.get('教学用途', '')
    
    # 检查是否包含"分步"、"乘法"、"计数"、"排列组合"等
    if ('分步' in filename or '分步' in title or 
        '计数' in filename or '计数' in title or
        '排列' in filename or '排列' in title or
        '组合' in filename or '组合' in title):
        counting_principle_all.append({
            '文件名': filename,
            '标题': title[:80],
            '教学用途': teaching_use,
        })

print(f"\n总共找到 {len(counting_principle_all)} 个分步乘法计数原理相关课件，教学用途分布:")
use_count = {}
for cw in counting_principle_all:
    use = cw['教学用途']
    use_count[use] = use_count.get(use, 0) + 1

for use, count in sorted(use_count.items(), key=lambda x: -x[1]):
    print(f"  {use}: {count}个")

print("\n详细列表:")
for i, cw in enumerate(counting_principle_all, 1):
    print(f"{i}. {cw['文件名']}")
    print(f"   标题: {cw['标题']}")
    print(f"   教学用途: {cw['教学用途']}")
    print()

if len(counting_principle_all) == 0:
    print("未找到任何分步乘法计数原理相关的课件")
