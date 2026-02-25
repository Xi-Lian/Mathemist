"""
测试意图识别修复

验证"帮我生成一份指数函数的教案，第一课时"是否被正确识别为教案生成意图
"""

from app.core.intent_analyzer import IntentAnalyzer

def test_intent_recognition():
    """测试意图识别"""
    
    analyzer = IntentAnalyzer()
    
    # 测试用例
    test_cases = [
        {
            "input": "帮我生成一份指数函数的教案，第一课时",
            "expected_intent": "generate_lesson_plan",
            "description": "生成教案（包含'帮我'和'生成'，应该识别为教案生成）"
        },
        {
            "input": "生成指数函数的教案",
            "expected_intent": "generate_lesson_plan",
            "description": "生成教案（只有'生成'，应该识别为教案生成）"
        },
        {
            "input": "帮我找一下指数函数的教案",
            "expected_intent": "generate_lesson_plan",
            "description": "找教案（包含'帮我'和'教案'，应该识别为教案生成）"
        },
        {
            "input": "查找指数函数的习题",
            "expected_intent": "search",
            "description": "查找习题（应该识别为搜索）"
        },
        {
            "input": "给我指数函数的资料",
            "expected_intent": "search",
            "description": "给资料（应该识别为搜索）"
        }
    ]
    
    print("=" * 80)
    print("意图识别测试")
    print("=" * 80)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}: {test_case['description']}")
        print(f"输入: {test_case['input']}")
        print(f"期望意图: {test_case['expected_intent']}")
        
        # 分析意图
        result = analyzer.analyze(test_case['input'])
        actual_intent = result.get('intent')
        
        print(f"实际意图: {actual_intent}")
        
        # 验证结果
        if actual_intent == test_case['expected_intent']:
            print("✅ 测试通过")
        else:
            print("❌ 测试失败")
            all_passed = False
        
        # 打印详细信息
        print(f"用户需求: {result.get('user_needs')}")
        print(f"资源类型: {result.get('resource_types')}")
    
    print("\n" + "=" * 80)
    if all_passed:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败")
    print("=" * 80)
    
    return all_passed

if __name__ == "__main__":
    test_intent_recognition()
