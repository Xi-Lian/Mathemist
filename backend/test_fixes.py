#!/usr/bin/env python3
"""
测试脚本：验证系统修复效果

测试内容：
1. 指令词和主题词混淆问题
2. 生成教案和推送资源的场景混淆问题
3. 主题提取的精确度
4. 结果展示方式
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.query_preprocessor import QueryPreprocessor
from app.core.intent_analyzer import IntentAnalyzer
from app.core.resource_retriever import ResourceRetriever


def test_instruction_topic_confusion():
    """
    测试指令词和主题词混淆问题
    """
    print("\n" + "="*60)
    print("测试 1: 指令词和主题词混淆问题")
    print("="*60)
    
    test_cases = [
        "推送函数的概念教案",
        "给我指数函数的教学设计",
        "找二次函数的习题",
        "推荐三角函数的课件",
        "生成函数的概念教案",
        "设计指数函数的教学方案"
    ]
    
    preprocessor = QueryPreprocessor()
    analyzer = IntentAnalyzer()
    
    for query in test_cases:
        print(f"\n测试查询: {query}")
        
        # 测试查询预处理
        result = preprocessor.preprocess(query)
        intent = result.get('intent', {})
        topic = intent.get('topic', '')
        instruction_type = intent.get('instruction_type', '')
        
        print(f"  提取的主题: {topic}")
        print(f"  指令类型: {instruction_type}")
        
        # 测试意图分析
        intent_result = analyzer.analyze(query)
        primary_intent = intent_result.get('primary_intent', '')
        
        print(f"  主要意图: {primary_intent}")
        
        # 验证指令词没有被误当作主题词
        if any(keyword in topic for keyword in ["推送", "给", "找", "推荐", "生成", "设计"]):
            print(f"  ❌ 失败: 指令词被误当作主题词")
        else:
            print(f"  ✅ 成功: 指令词和主题词正确分离")


def test_scene_confusion():
    """
    测试生成教案和推送资源的场景混淆问题
    """
    print("\n" + "="*60)
    print("测试 2: 生成教案和推送资源的场景混淆问题")
    print("="*60)
    
    test_cases = [
        "推送函数的概念教案",  # 应该是资源检索
        "生成函数的概念教案",  # 应该是教案生成
        "给我指数函数的教学设计",  # 应该是资源检索
        "设计指数函数的教学方案"  # 应该是教案生成
    ]
    
    analyzer = IntentAnalyzer()
    
    for query in test_cases:
        print(f"\n测试查询: {query}")
        
        intent_result = analyzer.analyze(query)
        primary_intent = intent_result.get('primary_intent', '')
        
        print(f"  主要意图: {primary_intent}")
        
        # 验证场景判断是否正确
        if "推送" in query or "给" in query or "找" in query or "推荐" in query:
            if primary_intent == "search":
                print(f"  ✅ 成功: 资源获取指令正确识别为search意图")
            else:
                print(f"  ❌ 失败: 资源获取指令被识别为{primary_intent}意图")
        elif "生成" in query or "设计" in query or "写" in query or "创作" in query:
            if primary_intent == "generate_lesson_plan":
                print(f"  ✅ 成功: 内容生成指令正确识别为generate_lesson_plan意图")
            else:
                print(f"  ❌ 失败: 内容生成指令被识别为{primary_intent}意图")


def test_topic_extraction_precision():
    """
    测试主题提取的精确度
    """
    print("\n" + "="*60)
    print("测试 3: 主题提取的精确度")
    print("="*60)
    
    test_cases = [
        "函数的概念教案",
        "函数的应用教学设计",
        "指数函数的概念",
        "指数函数的图像和性质",
        "三角函数的应用"
    ]
    
    preprocessor = QueryPreprocessor()
    retriever = ResourceRetriever()
    
    for query in test_cases:
        print(f"\n测试查询: {query}")
        
        # 测试查询预处理
        result = preprocessor.preprocess(query)
        intent = result.get('intent', {})
        topic = intent.get('topic', '')
        
        print(f"  提取的主题: {topic}")
        
        # 测试资源检索中的主题提取
        core_theme = retriever._extract_core_theme(query)
        print(f"  资源检索提取的核心主题: {core_theme}")
        
        # 验证主题提取是否准确
        expected_themes = {
            "函数的概念教案": "函数的概念",
            "函数的应用教学设计": "函数的应用",
            "指数函数的概念": "指数函数的概念",
            "指数函数的图像和性质": "指数函数的图像和性质",
            "三角函数的应用": "三角函数的应用"
        }
        
        expected_theme = expected_themes.get(query, "")
        if expected_theme and expected_theme in topic:
            print(f"  ✅ 成功: 主题提取准确")
        else:
            print(f"  ❌ 失败: 主题提取不准确")


def main():
    """
    主测试函数
    """
    print("开始测试系统修复效果...")
    
    test_instruction_topic_confusion()
    test_scene_confusion()
    test_topic_extraction_precision()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
