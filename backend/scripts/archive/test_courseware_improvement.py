"""
课件检索改进测试脚本

用于验证新的三字段评估器是否正常工作
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.retrieval.evaluation.courseware_evaluator import get_courseware_evaluator


def test_courseware_evaluator():
    """测试课件评估器"""
    
    print("=" * 80)
    print("课件评估器测试")
    print("=" * 80)
    
    evaluator = get_courseware_evaluator()
    
    # 测试用例1：完整的课件资源
    print("\n【测试1】完整信息的课件 - 分类加法计数原理练习课")
    metadata1 = {
        '文件名': '分类加法计数原理-练习课课件.pptx',
        '教学用途': '练习课课件',
        '知识点': '分类加法计数原理',
        '章节': '第六章-计数原理',
        '年级': '高二',
        '内容': '''
        一、导入
        通过生活实例引入分类加法计数原理
        
        二、新知讲解
        分类加法计数原理的定义和公式
        
        三、例题
        例题1：从A地到B地有3条路...
        例题2：用数字1,2,3可以组成...
        
        四、练习
        练习题1-5
        
        五、总结
        本节课重点掌握分类加法计数原理的应用
        
        六、作业
        课本Pxx 习题1-3
        '''
    }
    
    score1, show1, details1 = evaluator.evaluate(
        metadata=metadata1,
        doc=metadata1['内容'],
        distance=0.3,
        core_theme='分类加法计数原理',
        query='给我找分类加法计数原理的练习课课件'
    )
    
    print(f"得分: {score1:.3f}, 展示: {show1}")
    print(f"权重: {details1['weights']}")
    assert show1 == True, "完整课件应该被展示"
    
    # 测试用例2：缺少教学用途的课件
    print("\n【测试2】缺少教学用途的课件")
    metadata2 = {
        '文件名': '指数函数.pptx',
        '教学用途': '',
        '知识点': '指数函数',
        '内容': '指数函数的定义和性质...'
    }
    
    score2, show2, details2 = evaluator.evaluate(
        metadata=metadata2,
        doc=metadata2['内容'],
        distance=0.5,
        core_theme='指数函数',
        query='指数函数的课件'
    )
    
    print(f"得分: {score2:.3f}, 展示: {show2}")
    print(f"权重调整: {details2['weights']}")
    # 权重应该重新分配
    
    # 测试用例3：用户明确要求复习课
    print("\n【测试3】用户明确要求复习课")
    metadata3 = {
        '文件名': '三角函数复习.pptx',
        '教学用途': '复习课课件',
        '知识点': '三角函数',
        '内容': '三角函数的复习总结...'
    }
    
    score3, show3, details3 = evaluator.evaluate(
        metadata=metadata3,
        doc=metadata3['内容'],
        distance=0.4,
        core_theme='三角函数',
        query='三角函数的复习课课件'
    )
    
    print(f"得分: {score3:.3f}, 展示: {show3}")
    print(f"权重调整: {details3['weights']}")
    # 教学用途权重应该提高
    
    print("\n" + "=" * 80)
    print("✅ 所有测试通过！")
    print("=" * 80)


if __name__ == '__main__':
    try:
        test_courseware_evaluator()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
