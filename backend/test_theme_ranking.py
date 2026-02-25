#!/usr/bin/env python3
"""
测试脚本：验证主题匹配和排序修复效果

测试内容：
1. 主题匹配的精确度
2. 排序逻辑（主题匹配优先）
3. "函数的概念"是否排在"函数的应用"前面
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor


def test_theme_ranking():
    """
    测试主题排序逻辑
    """
    print("\n" + "="*60)
    print("测试: 主题匹配和排序修复效果")
    print("="*60)
    
    test_queries = [
        "函数的概念教案",
        "推送函数的概念教案",
        "给我函数的概念教学设计"
    ]
    
    preprocessor = QueryPreprocessor()
    retriever = ResourceRetriever()
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        
        # 预处理查询
        preprocessed = preprocessor.preprocess(query)
        intent = preprocessed.get('intent', {})
        topic = intent.get('topic', '')
        print(f"  提取的主题: {topic}")
        
        # 检索资源
        results = retriever.retrieve(query, intent='search', resource_types=['教案'])
        
        # 检查教案资源
        lesson_plans = results.get('lesson_plan_patterns', [])
        print(f"  找到教案资源数量: {len(lesson_plans)}")
        
        # 显示排序结果
        if lesson_plans:
            print(f"\n  排序结果:")
            for i, plan in enumerate(lesson_plans[:5], 1):
                title = plan.get('title', '未知')
                relevance = plan.get('relevance', 0)
                base_relevance = plan.get('base_relevance', 0)
                theme_match = plan.get('theme_match', False)
                theme_boost = plan.get('theme_boost', 0)
                
                match_label = "【主题精确匹配】" if theme_match else "【主题相关】"
                print(f"  {i}. {match_label} {title} - 相似度: {relevance:.1%} (基础: {base_relevance:.1%} 主题加分: {theme_boost:.1%})")
            
            # 验证排序是否正确
            verify_ranking(lesson_plans, topic)


def verify_ranking(resources, expected_theme):
    """
    验证排序是否正确
    
    Args:
        resources: 资源列表
        expected_theme: 期望的主题
    """
    # 检查主题精确匹配的资源是否排在前面
    has_theme_match = False
    first_theme_match_index = -1
    
    for i, resource in enumerate(resources):
        if resource.get('theme_match', False):
            has_theme_match = True
            first_theme_match_index = i
            break
    
    if has_theme_match:
        if first_theme_match_index == 0:
            print(f"  ✅ 成功: 主题精确匹配的资源排在第一位")
        else:
            print(f"  ❌ 失败: 主题精确匹配的资源排在第{first_theme_match_index + 1}位，应该排在第一位")
    else:
        print(f"  ⚠️ 警告: 没有找到主题精确匹配的资源")
    
    # 特殊验证：函数的概念是否排在函数的应用前面
    if expected_theme == "函数的概念":
        concept_index = -1
        application_index = -1
        
        for i, resource in enumerate(resources):
            title = resource.get('title', '').lower()
            if '函数的概念' in title or '函数概念' in title:
                concept_index = i
            elif '函数的应用' in title or '函数应用' in title:
                application_index = i
        
        if concept_index != -1 and application_index != -1:
            if concept_index < application_index:
                print(f"  ✅ 成功: '函数的概念'排在'函数的应用'前面")
            else:
                print(f"  ❌ 失败: '函数的概念'排在'函数的应用'后面")
        elif concept_index != -1:
            print(f"  ✅ 成功: 找到'函数的概念'资源，未找到'函数的应用'资源")
        else:
            print(f"  ⚠️ 警告: 未找到'函数的概念'资源")


def test_core_theme_extraction():
    """
    测试核心主题提取
    """
    print("\n" + "="*60)
    print("测试: 核心主题提取")
    print("="*60)
    
    test_queries = [
        "函数的概念教案",
        "函数的应用教学设计",
        "函数的性质课件",
        "函数的表示法习题"
    ]
    
    retriever = ResourceRetriever()
    
    for query in test_queries:
        core_theme = retriever._extract_core_theme(query)
        print(f"  查询: {query} -> 提取的核心主题: {core_theme}")


def main():
    """
    主测试函数
    """
    print("开始测试主题匹配和排序修复效果...")
    
    test_core_theme_extraction()
    test_theme_ranking()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
