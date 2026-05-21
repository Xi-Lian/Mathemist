"""
测试教学用途意图匹配改进
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

def test_teaching_use_intent():
    """测试教学用途意图匹配"""
    
    print("=" * 80)
    print("测试教学用途意图匹配改进")
    print("=" * 80)
    
    evaluator = get_courseware_evaluator()
    
    query = "我想要棱柱的练习课课件"
    core_theme = "棱柱"
    distance = 0.5
    
    # 测试1：练习课课件（应该高分）
    print("\n【测试1】练习课课件 - 应该高分")
    print("-" * 80)
    practice_courseware = {
        '文件名': '8.1课时1 棱柱、棱锥和棱台',
        '教学用途': '练习课课件',
        '内容': '课时1 棱柱、棱锥和棱台',
        '知识点': '',
    }
    score1, show1, details1 = evaluator.evaluate(
        metadata=practice_courseware,
        doc=practice_courseware['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score1:.3f}")
    print(f"教学用途得分: {details1['teaching_use_score']:.3f}")
    print(f"是否显示: {show1}")
    
    # 测试2：新授课课件（应该低分，因为用户要练习课）
    print("\n【测试2】新授课课件 - 应该低分（不匹配用户意图）")
    print("-" * 80)
    new_lesson_courseware = {
        '文件名': '8.1 基本立体图形',
        '教学用途': '新授课课件',
        '内容': '8.1 基本立体图形 第1课时 棱柱、棱锥、棱台的结构特征',
        '知识点': '',
    }
    score2, show2, details2 = evaluator.evaluate(
        metadata=new_lesson_courseware,
        doc=new_lesson_courseware['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score2:.3f}")
    print(f"教学用途得分: {details2['teaching_use_score']:.3f}")
    print(f"是否显示: {show2}")
    
    # 测试3：复习课课件（也应该低分）
    print("\n【测试3】复习课课件 - 应该低分（不匹配用户意图）")
    print("-" * 80)
    review_courseware = {
        '文件名': '立体几何复习',
        '教学用途': '复习课课件',
        '内容': '立体几何综合复习',
        '知识点': '',
    }
    score3, show3, details3 = evaluator.evaluate(
        metadata=review_courseware,
        doc=review_courseware['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query
    )
    print(f"最终得分: {score3:.3f}")
    print(f"教学用途得分: {details3['teaching_use_score']:.3f}")
    print(f"是否显示: {show3}")
    
    # 测试4：没有明确意图的查询
    print("\n【测试4】无明确意图查询 - 新授课应该中等分数")
    print("-" * 80)
    query_no_intent = "棱柱的课件"
    score4, show4, details4 = evaluator.evaluate(
        metadata=new_lesson_courseware,
        doc=new_lesson_courseware['内容'],
        distance=distance,
        core_theme=core_theme,
        query=query_no_intent
    )
    print(f"查询: {query_no_intent}")
    print(f"最终得分: {score4:.3f}")
    print(f"教学用途得分: {details4['teaching_use_score']:.3f}")
    print(f"是否显示: {show4}")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"练习课课件得分: {score1:.3f} (教学用途: {details1['teaching_use_score']:.3f})")
    print(f"新授课课件得分: {score2:.3f} (教学用途: {details2['teaching_use_score']:.3f})")
    print(f"复习课课件得分: {score3:.3f} (教学用途: {details3['teaching_use_score']:.3f})")
    
    print("\n预期结果:")
    print("  ✅ 练习课课件应该得分最高（>0.4）")
    print("  ✅ 新授课课件应该得分很低（<0.3），因为不匹配用户意图")
    print("  ✅ 复习课课件应该得分很低（<0.3），因为不匹配用户意图")
    
    if score1 > 0.4 and score2 < 0.3 and score3 < 0.3:
        print("\n🎉 测试通过！教学用途意图匹配改进有效。")
    else:
        print("\n⚠️ 测试未完全通过，需要进一步调整。")
        if score1 <= 0.4:
            print(f"  - 练习课课件得分{score1:.3f}偏低")
        if score2 >= 0.3:
            print(f"  - 新授课课件得分{score2:.3f}偏高（应该被惩罚）")
        if score3 >= 0.3:
            print(f"  - 复习课课件得分{score3:.3f}偏高（应该被惩罚）")

if __name__ == "__main__":
    test_teaching_use_intent()
