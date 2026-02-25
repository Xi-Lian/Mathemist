"""
测试教案生成流程

验证"帮我生成一份指数函数的教案，第一课时"是否能正确生成教案
"""

from app.core.unified_lesson_plan_system import unified_lesson_plan_system
from app.core.intent_analyzer import IntentAnalyzer

def test_lesson_plan_generation():
    """测试教案生成流程"""
    
    print("=" * 80)
    print("教案生成流程测试")
    print("=" * 80)
    
    # 1. 测试意图识别
    print("\n【步骤1】意图识别")
    analyzer = IntentAnalyzer()
    user_input = "帮我生成一份指数函数的教案，第一课时"
    
    intent_result = analyzer.analyze(user_input)
    print(f"用户输入: {user_input}")
    print(f"识别意图: {intent_result.get('intent')}")
    print(f"用户需求: {intent_result.get('user_needs')}")
    print(f"资源类型: {intent_result.get('resource_types')}")
    
    if intent_result.get('intent') != 'generate_lesson_plan':
        print("❌ 意图识别失败")
        return False
    else:
        print("✅ 意图识别正确")
    
    # 2. 测试统一教案系统
    print("\n【步骤2】统一教案系统处理")
    result = unified_lesson_plan_system.process_lesson_plan_request(user_input)
    
    print(f"处理状态: {result.get('status')}")
    print(f"会话ID: {result.get('session_id')}")
    print(f"教案状态: {result.get('lesson_plan_status')}")
    print(f"已收集信息: {result.get('lesson_plan_collected_info')}")
    
    # 3. 检查响应内容
    print("\n【步骤3】响应内容检查")
    response = result.get('response', '')
    
    if not response:
        print("❌ 响应为空")
        return False
    
    print(f"响应长度: {len(response)}字符")
    print(f"响应前200字符: {response[:200]}...")
    
    # 检查响应类型
    if '教案资源' in response and '相关教学资源' in response:
        print("❌ 响应显示的是检索到的资源，而不是引导信息或生成的教案")
        return False
    elif '为了生成更完善的教案' in response or '我还需要了解' in response:
        print("✅ 响应是引导用户补充信息")
        return True
    elif '生成的教案' in response or '教学目标' in response or '教学过程' in response:
        print("✅ 响应是生成的教案")
        return True
    else:
        print("⚠️ 响应类型未知")
        return False

if __name__ == "__main__":
    success = test_lesson_plan_generation()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ 测试通过")
    else:
        print("❌ 测试失败")
    print("=" * 80)
