"""
测试核心主题提取
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

# 模拟查询
query = '找一下向量的运算的练习课课件'

print("=" * 80)
print("查询分析")
print("=" * 80)
print(f"查询: {query}\n")

# 检查意图识别
from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator
evaluator = get_courseware_evaluator()

intent = evaluator._extract_teaching_intent_from_query(query)
print(f"识别的教学意图: {intent}")

keywords = evaluator._extract_meaningful_keywords(query)
print(f"提取的关键词: {keywords}\n")

# 检查课件2的字段是否包含关键词
metadata2 = {
    '文件名': '6.2.1 向量的加法运算＋6.2.2 向量的减法运算',
    'title': '6.2.1 向量的加法运算＋6.2.2 向量的减法运算 - 6.2.1 向量的加法运算＋6.2.2',
    '教学用途': '练习课课件',
}

print("=" * 80)
print("课件2字段检查")
print("=" * 80)
print(f"文件名: {metadata2['文件名']}")
print(f"标题: {metadata2['title']}\n")

# 检查是否包含"向量"
print(f"文件名包含'向量': {'向量' in metadata2['文件名']}")
print(f"标题包含'向量': {'向量' in metadata2['title']}")

# 检查是否包含"运算"
print(f"文件名包含'运算': {'运算' in metadata2['文件名']}")
print(f"标题包含'运算': {'运算' in metadata2['title']}")

print("\n" + "=" * 80)
print("问题分析")
print("=" * 80)
print("核心主题可能是'平面向量的运算'或'向量的运算'")
print("但课件的文件名和标题中只包含'向量'和'运算'，不包含完整的'向量的运算'")
print("这导致早期拒绝机制认为不匹配，直接过滤掉了！")
