"""
测试向量运算课件的评分
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

evaluator = get_courseware_evaluator()

query = '找一下向量的运算的练习课课件'
core_theme = '平面向量的运算, 向量的运算'
distance = 0.5

# 课件1：新授课（当前返回的错误结果）
metadata1 = {
    '文件名': '6.2.1向量的加法运算_课件',
    'title': '6.2.1向量的加法运算_课件 - 6.2 平面向量的运算（1）',
    '教学用途': '新授课课件',
    '内容': '6.2 平面向量的运算（1）',
}

score1, show1, details1 = evaluator.evaluate(
    metadata=metadata1,
    doc=metadata1['内容'],
    distance=distance,
    core_theme=core_theme,
    query=query
)

# 课件2：练习课（期望的正确结果）
metadata2 = {
    '文件名': '6.2.1 向量的加法运算＋6.2.2 向量的减法运算',
    'title': '6.2.1 向量的加法运算＋6.2.2 向量的减法运算 - 6.2.1 向量的加法运算＋6.2.2',
    '教学用途': '练习课课件',
    '内容': '6.2.1 向量的加法运算＋6.2.2 向量的减法运算',
}

score2, show2, details2 = evaluator.evaluate(
    metadata=metadata2,
    doc=metadata2['内容'],
    distance=distance,
    core_theme=core_theme,
    query=query
)

print("=" * 80)
print("向量运算课件评分对比")
print("=" * 80)

print("\n【课件1】新授课（错误结果）")
print("-" * 80)
print(f"文件名: {metadata1['文件名']}")
print(f"教学用途: {metadata1['教学用途']}")
print(f"文件名字段得分: {details1['filename_score']:.3f}")
print(f"教学用途字段得分: {details1['teaching_use_score']:.3f}")
print(f"内容字段得分: {details1['content_score']:.3f}")
print(f"最终得分: {score1:.3f}")
print(f"是否展示: {show1}")

print("\n【课件2】练习课（正确结果）")
print("-" * 80)
print(f"文件名: {metadata2['文件名']}")
print(f"教学用途: {metadata2['教学用途']}")
print(f"文件名字段得分: {details2['filename_score']:.3f}")
print(f"教学用途字段得分: {details2['teaching_use_score']:.3f}")
print(f"内容字段得分: {details2['content_score']:.3f}")
print(f"最终得分: {score2:.3f}")
print(f"是否展示: {show2}")

print("\n" + "=" * 80)
print("分析")
print("=" * 80)
print(f"课件2比课件1高: {score2 - score1:.3f} 分")
print(f"教学用途得分差距: {details2['teaching_use_score'] - details1['teaching_use_score']:.3f} 分")

if score2 > score1 and show2:
    print("\n✅ 评分合理！练习课课件得分更高。")
else:
    print("\n❌ 评分不合理！需要调整。")
    if show1 and not show2:
        print("   问题：新授课被展示，练习课被过滤！")
