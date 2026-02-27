#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试改进后的教案生成系统功能

测试内容：
1. 理论卡片索引和引用验证
2. 指令词智能理解
3. 分级完整度评估和"直接生成"选项
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.lesson_plan_generator import LessonPlanGenerator
from app.core.unified_lesson_plan_system import UnifiedLessonPlanSystem


def test_theory_cards_index():
    """测试理论卡片索引功能"""
    print("\n=== 测试理论卡片索引功能 ===")
    
    generator = LessonPlanGenerator()
    
    # 检查理论卡片索引是否成功创建
    if hasattr(generator, 'theory_cards_index'):
        print(f"✅ 理论卡片索引创建成功，包含 {len(generator.theory_cards_index)} 个理论卡片")
        
        # 打印前几个理论卡片的信息
        print("\n📚 部分理论卡片信息：")
        for i, (card_key, card_info) in enumerate(list(generator.theory_cards_index.items())[:3]):
            print(f"\n{card_key}：{card_info['name']}")
            print(f"  核心观点：{card_info['core_view'][:50]}...")
            print(f"  适用环节：{card_info['applicable_links']}")
            print(f"  教学启发：{card_info['teaching_inspiration'][:50]}...")
    else:
        print("❌ 理论卡片索引创建失败")


def test_command_word_detection():
    """测试指令词智能理解功能"""
    print("\n=== 测试指令词智能理解功能 ===")
    
    system = UnifiedLessonPlanSystem()
    
    # 测试用例
    test_cases = [
        "帮我生成一份指数函数教案",
        "生成指数函数的教案",
        "帮我找一下指数函数的教案",
        "查找指数函数的习题"
    ]
    
    for i, test_input in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {test_input}")
        result = system.process_lesson_plan_request(test_input)
        
        if 'status' in result:
            if result['status'] == 'error':
                print(f"  结果：{result['message']}")
            elif result['status'] == 'guiding':
                print(f"  结果：引导用户补充信息")
                print(f"  提示：{result['response'][:100]}...")
            else:
                print(f"  结果：{result.get('status', '未知')}")
        else:
            print(f"  结果：{result.get('success', False)}")


def test_direct_generate_option():
    """测试"直接生成"选项"""
    print("\n=== 测试'直接生成'选项 ===")
    
    system = UnifiedLessonPlanSystem()
    
    # 先发送一个信息不完整的请求
    test_input = "指数函数"
    result1 = system.process_lesson_plan_request(test_input)
    session_id = result1.get('session_id')
    
    print(f"\n1. 初始请求：{test_input}")
    print(f"   结果：{result1.get('status')}")
    
    # 然后发送"直接生成"请求
    if session_id:
        direct_input = "直接生成"
        result2 = system.process_lesson_plan_request(direct_input, session_id)
        
        print(f"\n2. 发送'直接生成'请求")
        if result2.get('success'):
            print(f"   结果：成功")
            if 'lesson_plan' in result2:
                print(f"   教案生成成功，长度：{len(result2['lesson_plan'])}字符")
        else:
            print(f"   结果：失败 - {result2.get('message', '未知错误')}")


if __name__ == "__main__":
    print("🚀 开始测试改进后的教案生成系统功能")
    
    # 测试理论卡片索引
    test_theory_cards_index()
    
    # 测试指令词智能理解
    test_command_word_detection()
    
    # 测试"直接生成"选项
    test_direct_generate_option()
    
    print("\n✅ 测试完成")
