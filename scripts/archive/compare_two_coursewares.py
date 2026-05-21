"""
对比两个课件的评分差异
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

evaluator = get_courseware_evaluator()

query = '我想要棱柱的练习课课件'
core_theme = '棱柱'
distance = 0.5

# 课件1：文件名包含"棱柱"
metadata1 = {
    '文件名': '8.1课时1 棱柱、棱锥和棱台',
    'title': '8.1课时1 棱柱、棱锥和棱台 - 课时1 棱柱、棱锥和棱台',
    '教学用途': '练习课课件',
    '内容': '课时1 棱柱、棱锥和棱台',
}

score1, show1, details1 = evaluator.evaluate(
    metadata=metadata1,
    doc=metadata1['内容'],
    distance=distance,
    core_theme=core_theme,
    query=query
)

# 课件2：文件名不包含"棱柱"，但标题和内容包含
metadata2 = {
    '文件名': '8.1课时2 圆柱、圆锥、圆台和球',
    'title': '8.1课时2 圆柱、圆锥、圆台和球 - 课时2 棱柱、棱锥、圆台和球',
    '教学用途': '练习课课件',
    '内容': '课时2 棱柱、棱锥、圆台和球',
}

score2, show2, details2 = evaluator.evaluate(
    metadata=metadata2,
    doc=metadata2['内容'],
    distance=distance,
    core_theme=core_theme,
    query=query
)

print("=" * 80)
print("两个课件的评分对比")
print("=" * 80)

print("\n【课件1】文件名包含'棱柱'")
print("-" * 80)
print(f"文件名: {metadata1['文件名']}")
print(f"文件名字段得分: {details1['filename_score']:.3f}")
print(f"教学用途字段得分: {details1['teaching_use_score']:.3f}")
print(f"内容字段得分: {details1['content_score']:.3f}")
print(f"最终得分: {score1:.3f}")
print(f"是否展示: {show1}")

print("\n【课件2】文件名不包含'棱柱'，但标题和内容包含")
print("-" * 80)
print(f"文件名: {metadata2['文件名']}")
print(f"文件名字段得分: {details2['filename_score']:.3f}")
print(f"教学用途字段得分: {details2['teaching_use_score']:.3f}")
print(f"内容字段得分: {details2['content_score']:.3f}")
print(f"最终得分: {score2:.3f}")
print(f"是否展示: {show2}")

print("\n" + "=" * 80)
print("分析")
print("=" * 80)
print(f"课件1比课件2高: {score1 - score2:.3f} 分")
print(f"文件名得分差距: {details1['filename_score'] - details2['filename_score']:.3f} 分")

if score1 > score2:
    print("\n✅ 评分合理！文件名包含核心主题的课件得分更高。")
    print("   这符合用户期望：更相关的资源排在前面。")
else:
    print("\n❌ 评分不合理！需要调整。")
