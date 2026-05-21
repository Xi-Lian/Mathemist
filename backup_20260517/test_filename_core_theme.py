"""
测试文件名核心主题匹配改进
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

def test_filename_core_theme_matching():
    """测试文件名核心主题匹配"""
    
    print("=" * 80)
    print("测试文件名核心主题匹配改进")
    print("=" * 80)
    
    evaluator = get_courseware_evaluator()
    
    query = "我想要棱柱的练习课课件"
    core_theme = "棱柱"
    distance = 0.5
    
    # 测试1：文件名包含核心主题（应该高分）
    print("\n【测试1】文件名包含核心主题'棱柱'")
    print("-" * 80)
    courseware_1 = {
        '文件名': '8.1课时1 棱柱、棱锥和棱台',
        '教学用途': '练习课课件',
        '内容': '课时1 棱柱、棱锥和棱台',
    }
    score1, show1, details1 = evaluator.evaluate(
        metadata=courseware_1,
        doc=courseware_1['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score1:.3f}")
    print(f"文件名字段得分: {details1['filename_score']:.3f}")
    print(f"是否显示: {show1}")
    
    # 测试2：文件名不包含核心主题，但包含相关词（应该低分）
    print("\n【测试2】文件名不包含'棱柱'，只包含'圆柱'")
    print("-" * 80)
    courseware_2 = {
        '文件名': '8.1课时2 圆柱、圆锥、圆台和球',
        '教学用途': '练习课课件',
        '内容': '课时2 圆柱、圆锥、圆台和球',
    }
    score2, show2, details2 = evaluator.evaluate(
        metadata=courseware_2,
        doc=courseware_2['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score2:.3f}")
    print(f"文件名字段得分: {details2['filename_score']:.3f}")
    print(f"是否显示: {show2}")
    
    # 测试3：文件名完全不相关（应该很低分）
    print("\n【测试3】文件名完全不相关")
    print("-" * 80)
    courseware_3 = {
        '文件名': '函数单调性讲解',
        '教学用途': '新授课课件',
        '内容': '函数单调性的定义和性质',
    }
    score3, show3, details3 = evaluator.evaluate(
        metadata=courseware_3,
        doc=courseware_3['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score3:.3f}")
    print(f"文件名字段得分: {details3['filename_score']:.3f}")
    print(f"是否显示: {show3}")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"测试1（包含'棱柱'）: 文件名得分={details1['filename_score']:.3f}, 总分={score1:.3f}")
    print(f"测试2（包含'圆柱'）: 文件名得分={details2['filename_score']:.3f}, 总分={score2:.3f}")
    print(f"测试3（完全不相关）: 文件名得分={details3['filename_score']:.3f}, 总分={score3:.3f}")
    
    print("\n预期结果:")
    print("  ✅ 测试1应该得分最高（文件名包含核心主题）")
    print("  ✅ 测试2应该得分较低（文件名不包含核心主题，即使教学用途匹配）")
    print("  ✅ 测试3应该得分最低（完全不相关）")
    
    if details1['filename_score'] > details2['filename_score'] and details2['filename_score'] > details3['filename_score']:
        print("\n🎉 测试通过！文件名核心主题匹配改进有效。")
        print(f"   差距: 测试1比测试2高 {details1['filename_score'] - details2['filename_score']:.3f} 分")
    else:
        print("\n⚠️ 测试未完全通过，需要进一步调整。")

if __name__ == "__main__":
    test_filename_core_theme_matching()
