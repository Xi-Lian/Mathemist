#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试教案内容处理是否完整（不再截断）
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.smart_content_processor import SmartContentProcessor


def test_lesson_plan_no_truncation():
    """测试教案内容处理是否完整（不再截断）"""
    print("\n=== 测试教案内容处理（不再截断）===")
    
    processor = SmartContentProcessor()
    
    # 创建一个较长的教案内容
    long_lesson_plan = """
教学目标：
1. 理解二次函数的概念和性质，掌握二次函数的图像绘制方法
2. 能够应用二次函数解决实际问题，培养数学建模能力
3. 通过探究活动，培养学生的逻辑思维能力和创新意识

教学重难点：
重点：二次函数的图像和性质，二次函数顶点坐标的求法
难点：二次函数在实际问题中的应用，二次函数与一元二次方程的关系

教学方法：
采用探究式教学法、合作学习法和情境教学法相结合的方式

导入：
通过实际问题引入二次函数：某商场销售一种商品，每件成本为20元，售价为30元时，每天可销售100件。若每涨价1元，每天少销售5件。求售价定为多少元时，每天利润最大？

新课讲授：
1. 二次函数的概念：形如y=ax²+bx+c(a≠0)的函数叫做二次函数
2. 二次函数的图像：抛物线，当a>0时开口向上，当a<0时开口向下
3. 二次函数的性质：顶点坐标、对称轴、最值等
4. 二次函数顶点坐标公式：(-b/2a, (4ac-b²)/4a)

巩固练习：
1. 求下列二次函数的顶点坐标和对称轴
   (1) y=x²-2x+3  (2) y=-2x²+4x-1
2. 已知二次函数y=ax²+bx+c的图像经过点(0,1)、(1,2)、(2,5)，求这个二次函数的解析式

小结：
总结本节课学习的主要内容：二次函数的概念、图像、性质及其应用

作业：
1. 完成课后习题1-5题
2. 预习下一节课内容：二次函数的应用
"""
    
    print(f"\n原始教案长度：{len(long_lesson_plan)} 字符")
    
    # 处理教案内容
    result = processor._process_lesson_plan(long_lesson_plan, max_length=300)
    
    print(f"\n处理后摘要长度：{result['processed_length']} 字符")
    print(f"原始长度：{result['original_length']} 字符")
    print(f"是否有更多内容：{result['has_more']}")
    print(f"资源类型：{result['resource_type']}")
    
    # 验证内容是否完整（允许少量字符差异，因为清理空白字符）
    length_diff = abs(result['processed_length'] - result['original_length'])
    if length_diff <= 20:  # 允许最多20字符的差异（用于清理空白字符）
        print(f"\n✅ 测试通过：教案内容完整输出（差异{length_diff}字符，为空白字符清理）")
    else:
        print(f"\n❌ 测试失败：教案内容被截断，原始{result['original_length']}字符，处理后{result['processed_length']}字符，差异{length_diff}字符")
    
    # 打印处理后的内容（前500字符）
    print(f"\n处理后的内容（前500字符）：\n{result['summary'][:500]}...")
    
    # 检查是否包含所有关键部分（根据实际测试数据调整）
    key_sections = ["教学目标", "教学重难点", "教学方法", "导入", "新课讲授", "巩固练习", "小结", "作业"]
    missing_sections = []
    for section in key_sections:
        if section not in result['summary']:
            missing_sections.append(section)
    
    if missing_sections:
        print(f"\n⚠️  缺失的部分：{', '.join(missing_sections)}")
    else:
        print(f"\n✅ 所有关键部分都完整保留")


def test_response_builder_lesson_plan():
    """测试ResponseBuilder中教案资源的处理"""
    print("\n=== 测试ResponseBuilder中教案资源的处理 ===")
    
    from app.core.response_builder import ResponseBuilder
    
    builder = ResponseBuilder()
    
    # 初始化content_processor
    builder.content_processor = builder.model_config.get_content_processor()
    
    # 测试教案资源
    lesson_plan_content = """
教学目标：
1. 理解函数单调性的概念
2. 掌握判断函数单调性的方法
3. 能够应用函数单调性解决实际问题

教学重难点：
重点：函数单调性的概念和判断方法
难点：函数单调性的证明

教学过程：
一、导入：通过图像观察函数的变化趋势
二、新课讲授：讲解函数单调性的定义和判断方法
三、巩固练习：完成相关练习题
四、小结：总结本节课内容
"""
    
    print(f"\n原始教案长度：{len(lesson_plan_content)} 字符")
    
    # 处理教案资源
    processed_content = builder._process_resource_content("教案资源", "函数的单调性", lesson_plan_content)
    
    print(f"\n处理后长度：{len(processed_content)} 字符")
    
    # 验证内容是否完整
    if len(processed_content) == len(lesson_plan_content):
        print("\n✅ 测试通过：教案资源内容完整输出，未被截断")
    else:
        print(f"\n❌ 测试失败：教案资源内容被截断，原始{len(lesson_plan_content)}字符，处理后{len(processed_content)}字符")
    
    # 打印处理后的内容
    print(f"\n处理后的内容：\n{processed_content}")


if __name__ == "__main__":
    print("🚀 开始测试教案内容完整输出（不再截断）")
    
    # 测试SmartContentProcessor的教案处理
    test_lesson_plan_no_truncation()
    
    # 测试ResponseBuilder的教案资源处理
    test_response_builder_lesson_plan()
    
    print("\n✅ 测试完成")
