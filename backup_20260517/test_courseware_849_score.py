"""
测试courseware_849的实际评分
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

evaluator = get_courseware_evaluator()

# courseware_849的元数据
metadata = {
    '文件名': '8.1课时2 圆柱、圆锥、圆台和球',
    'title': '8.1课时2 圆柱、圆锥、圆台和球 - 课时2 棱柱、棱锥、圆台和球',  # V41.7: 添加title字段
    '教学用途': '练习课课件',
    '内容': '课时2 棱柱、棱锥、圆台和球',
}

doc = '课时2 棱柱、棱锥、圆台和球'
distance = 0.5  # 假设距离
core_theme = '棱柱'
query = '我想要棱柱的练习课课件'

score, should_show, details = evaluator.evaluate(
    metadata=metadata,
    doc=doc,
    distance=distance,
    core_theme=core_theme,
    query=query
)

print("=" * 80)
print("courseware_849 评分详情")
print("=" * 80)
print(f"文件名: {metadata['文件名']}")
print(f"教学用途: {metadata['教学用途']}")
print(f"内容: {metadata['内容']}")
print(f"\n核心主题: {core_theme}")
print(f"查询: {query}\n")

print(f"基础向量得分: {details['base_relevance']:.3f}")
print(f"文件名字段得分: {details['filename_score']:.3f}")
print(f"教学用途字段得分: {details['teaching_use_score']:.3f}")
print(f"内容字段得分: {details['content_score']:.3f}")
print(f"权重: {details['weights']}")
print(f"\n最终得分: {score:.3f}")
print(f"阈值: {details['threshold']:.3f}")
print(f"是否展示: {should_show}")

print("\n" + "=" * 80)
print("分析")
print("=" * 80)
if details['filename_score'] == 0:
    print("✅ 文件名不包含'棱柱'，得分为0（正确）")
else:
    print(f"❌ 文件名得分{details['filename_score']:.3f}，应该为0")

if details['content_score'] > 0.5:
    print(f"⚠️ 内容字段得分较高({details['content_score']:.3f})，因为内容包含'棱柱'")
    
if score > 0.5:
    print(f"⚠️ 最终得分{score:.3f}较高，可能会被返回")
else:
    print(f"✅ 最终得分{score:.3f}较低，应该被过滤")
