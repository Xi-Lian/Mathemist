"""
课件评估器系统性改进测试 - 验证改进是否适用于各种场景
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator

def test_systematic_improvements():
    """系统性改进测试"""
    
    print("=" * 80)
    print("课件评估器系统性改进测试")
    print("=" * 80)
    
    evaluator = get_courseware_evaluator()
    
    # 测试场景1：短内容但高信息密度的课件（标题式课件）
    print("\n【场景1】短内容 + 高信息密度（标题式课件）")
    print("-" * 80)
    short_high_density = {
        '文件名': '8.1课时1 棱柱、棱锥和棱台',
        '教学用途': '练习课课件',
        '内容': '课时1 棱柱、棱锥和棱台',  # 12字，但包含3个关键词
        '知识点': '',
    }
    score1, show1, details1 = evaluator.evaluate(
        metadata=short_high_density,
        doc=short_high_density['内容'],
        distance=0.5,
        core_theme='棱柱',
        query='我想要棱柱的练习课课件'
    )
    print(f"得分: {score1:.3f} {'[PASS]' if show1 else '[FAIL]'}")
    print(f"  - 文件名得分: {details1['filename_score']:.3f}")
    print(f"  - 教学用途得分: {details1['teaching_use_score']:.3f}")
    print(f"  - 内容得分: {details1['content_score']:.3f}")
    print(f"  - 阈值: {details1['threshold']:.3f}")
    
    # 测试场景2：短内容且低信息密度的课件
    print("\n【场景2】短内容 + 低信息密度")
    print("-" * 80)
    short_low_density = {
        '文件名': 'Untitled',
        '教学用途': '',
        '内容': '这是一个测试',  # 6字，无数学关键词
        '知识点': '',
    }
    score2, show2, details2 = evaluator.evaluate(
        metadata=short_low_density,
        doc=short_low_density['内容'],
        distance=0.8,
        core_theme='函数',
        query='函数的教案'
    )
    print(f"得分: {score2:.3f} {'[PASS]' if show2 else '[FAIL]'}")
    print(f"  - 应该被过滤（质量太低）")
    
    # 测试场景3：中等长度内容（100-500字）
    print("\n【场景3】中等长度内容（100-500字）")
    print("-" * 80)
    medium_content = {
        '文件名': '函数单调性讲解',
        '教学用途': '新授课课件',
        '内容': '本节课讲解函数的单调性。首先介绍单调性的定义，然后通过例题演示如何判断函数的单调性。最后总结单调性的性质和应用。',  # 约60字
        '知识点': '函数单调性',
    }
    score3, show3, details3 = evaluator.evaluate(
        metadata=medium_content,
        doc=medium_content['内容'],
        distance=0.4,
        core_theme='函数',
        query='函数单调性的新授课'
    )
    print(f"得分: {score3:.3f} {'[PASS]' if show3 else '[FAIL]'}")
    print(f"  - 应该有合理的分数（不是0）")
    
    # 测试场景4：长内容且结构完整
    print("\n【场景4】长内容 + 结构完整")
    print("-" * 80)
    long_complete = {
        '文件名': '概率统计综合复习',
        '教学用途': '复习课课件',
        '内容': '''
        一、导入
        通过生活中的例子引入概率统计的概念。
        
        二、新知讲解
        1. 古典概型的定义和计算方法
        2. 条件概率的公式推导
        3. 独立事件的判定
        
        三、例题演示
        例题1：掷骰子问题
        例题2：抽球问题
        
        四、练习训练
        请同学们完成课后习题1-5
        
        五、课堂总结
        回顾本节课的重点内容
        
        六、作业布置
        完成练习册第20页
        ''',
        '知识点': '概率统计',
    }
    score4, show4, details4 = evaluator.evaluate(
        metadata=long_complete,
        doc=long_complete['内容'],
        distance=0.3,
        core_theme='概率',
        query='概率统计的复习课'
    )
    print(f"得分: {score4:.3f} {'[PASS]' if show4 else '[FAIL]'}")
    print(f"  - 应该获得高分")
    
    # 测试场景5：文件名精准匹配但内容为空
    print("\n【场景5】文件名精准匹配 + 内容为空")
    print("-" * 80)
    filename_only = {
        '文件名': '立体几何-棱柱的性质与判定',
        '教学用途': '新授课课件',
        '内容': '',  # 空内容
        '知识点': '',
    }
    score5, show5, details5 = evaluator.evaluate(
        metadata=filename_only,
        doc='',
        distance=0.5,
        core_theme='棱柱',
        query='棱柱的新授课'
    )
    print(f"得分: {score5:.3f} {'[PASS]' if show5 else '[FAIL]'}")
    print(f"  - 即使内容为空，文件名匹配好也应该通过")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    tests = [
        ("场景1：短内容+高密度", score1, show1, True),
        ("场景2：短内容+低密度", score2, show2, False),
        ("场景3：中等长度", score3, show3, True),
        ("场景4：长内容+完整", score4, show4, True),
        ("场景5：文件名精准", score5, show5, True),
    ]
    
    passed = 0
    for name, score, actual_show, expected_show in tests:
        status = "✅" if actual_show == expected_show else "❌"
        if actual_show == expected_show:
            passed += 1
        print(f"{status} {name}: 得分={score:.3f}, 显示={actual_show}, 期望={expected_show}")
    
    print(f"\n通过率: {passed}/{len(tests)} = {passed/len(tests)*100:.1f}%")
    
    if passed == len(tests):
        print("\n🎉 所有测试通过！改进具有通用性。")
    else:
        print(f"\n⚠️ 有{len(tests) - passed}个测试未通过，需要进一步调整。")

if __name__ == "__main__":
    test_systematic_improvements()
