"""
快速测试文件名评分逻辑
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

evaluator = get_courseware_evaluator()

# 测试文件名评分
filename1 = '8.1课时1 棱柱、棱锥和棱台'
filename2 = '8.1课时2 圆柱、圆锥、圆台和球'
core_theme = '棱柱'
query = '我想要棱柱的练习课课件'

score1 = evaluator._score_filename(filename1, core_theme, query)
score2 = evaluator._score_filename(filename2, core_theme, query)

print("=" * 80)
print("文件名评分测试")
print("=" * 80)
print(f"\n核心主题: {core_theme}")
print(f"查询: {query}\n")

print(f"文件名1: {filename1}")
print(f"  评分: {score1:.3f}")

print(f"\n文件名2: {filename2}")
print(f"  评分: {score2:.3f}")

print(f"\n差距: {score1 - score2:.3f}")

if score1 > score2:
    print("\n✅ 改进生效！包含核心主题的文件名得分更高。")
else:
    print("\n❌ 改进未生效！需要检查代码。")
