"""
测试棱柱课件评分 - 找出为什么得分低
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

def test_prism_courseware_scoring():
    """测试棱柱课件评分"""
    
    print("=" * 80)
    print("测试棱柱课件评分")
    print("=" * 80)
    
    evaluator = get_courseware_evaluator()
    
    # 模拟那两个目标课件的元数据
    target_courseware_1 = {
        '文件名': '8.1课时1 棱柱、棱锥和棱台',
        '教学用途': '练习课课件',
        '内容': '课时1 棱柱、棱锥和棱台',  # 简短的内容
        '知识点': '',  # 空的！
        '章节': '',
        '年级': ''
    }
    
    target_courseware_2 = {
        '文件名': '8.1课时2 圆柱、圆锥、圆台和球',
        '教学用途': '练习课课件',
        '内容': '课时2 圆柱、圆锥、圆台和球',  # 简短的内容
        '知识点': '',  # 空的！
        '章节': '',
        '年级': ''
    }
    
    # 对比一个已返回的课件
    returned_courseware = {
        '文件名': '8.1 基本立体图形',
        '教学用途': '',  # 可能也是空的
        '内容': '8.1 基本立体图形 第1课时 棱柱、棱锥、棱台的结构特征',  # 更详细的内容
        '知识点': '',
        '章节': '',
        '年级': ''
    }
    
    query = "我想要棱柱的练习课课件"
    core_theme = "棱柱"
    distance = 0.5  # 假设向量距离
    
    print(f"\n查询: {query}")
    print(f"核心主题: {core_theme}")
    print(f"向量距离: {distance}\n")
    
    # 测试目标课件1
    print("-" * 80)
    print("【目标课件1】8.1课时1 棱柱、棱锥和棱台")
    print("-" * 80)
    score1, show1, details1 = evaluator.evaluate(
        metadata=target_courseware_1,
        doc=target_courseware_1['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score1:.3f}")
    print(f"是否显示: {show1}")
    print(f"权重: {details1.get('weights', {})}")
    print(f"各字段得分:")
    print(f"  - 文件名: {details1.get('filename_score', 0):.3f}")
    print(f"  - 教学用途: {details1.get('teaching_use_score', 0):.3f}")
    print(f"  - 内容: {details1.get('content_score', 0):.3f}")
    print(f"  - 基础向量: {details1.get('base_relevance', 0):.3f}")
    
    # 测试目标课件2
    print("\n" + "-" * 80)
    print("【目标课件2】8.1课时2 圆柱、圆锥、圆台和球")
    print("-" * 80)
    score2, show2, details2 = evaluator.evaluate(
        metadata=target_courseware_2,
        doc=target_courseware_2['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score2:.3f}")
    print(f"是否显示: {show2}")
    print(f"权重: {details2.get('weights', {})}")
    print(f"各字段得分:")
    print(f"  - 文件名: {details2.get('filename_score', 0):.3f}")
    print(f"  - 教学用途: {details2.get('teaching_use_score', 0):.3f}")
    print(f"  - 内容: {details2.get('content_score', 0):.3f}")
    print(f"  - 基础向量: {details2.get('base_relevance', 0):.3f}")
    
    # 测试已返回的课件
    print("\n" + "-" * 80)
    print("【已返回课件】8.1 基本立体图形")
    print("-" * 80)
    score3, show3, details3 = evaluator.evaluate(
        metadata=returned_courseware,
        doc=returned_courseware['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score3:.3f}")
    print(f"是否显示: {show3}")
    print(f"权重: {details3.get('weights', {})}")
    print(f"各字段得分:")
    print(f"  - 文件名: {details3.get('filename_score', 0):.3f}")
    print(f"  - 教学用途: {details3.get('teaching_use_score', 0):.3f}")
    print(f"  - 内容: {details3.get('content_score', 0):.3f}")
    print(f"  - 基础向量: {details3.get('base_relevance', 0):.3f}")
    
    print("\n" + "=" * 80)
    print("分析结论:")
    print("=" * 80)
    print(f"目标课件1得分: {score1:.3f} {'✅ 通过' if show1 else '❌ 被过滤'}")
    print(f"目标课件2得分: {score2:.3f} {'✅ 通过' if show2 else '❌ 被过滤'}")
    print(f"已返回课件得分: {score3:.3f} {'✅ 通过' if show3 else '❌ 被过滤'}")
    
    if not show1 or not show2:
        print("\n问题诊断:")
        if not show1:
            print(f"  - 目标课件1被过滤，得分{score1:.3f}低于阈值")
        if not show2:
            print(f"  - 目标课件2被过滤，得分{score2:.3f}低于阈值")
        
        print("\n可能原因:")
        print("  1. 内容字段太短（只有标题），内容丰富度评分低")
        print("  2. 知识点字段为空，无法进行知识点覆盖度评估")
        print("  3. 动态权重调整后，内容字段的权重过高但得分低")

if __name__ == "__main__":
    test_prism_courseware_scoring()
