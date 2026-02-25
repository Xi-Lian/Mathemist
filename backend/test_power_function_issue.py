#!/usr/bin/env python3
"""
测试脚本：分析幂函数习题检索失败的问题

测试内容：
1. 查询预处理和主题提取
2. 资源检索和分类
3. 主题匹配逻辑
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.query_preprocessor import QueryPreprocessor
from app.core.resource_retriever import ResourceRetriever
from app.core.theme_matcher import get_theme_matcher


def test_query_preprocessing():
    """
    测试查询预处理和主题提取
    """
    print("\n" + "="*60)
    print("测试: 查询预处理和主题提取")
    print("="*60)
    
    test_queries = [
        "帮我找一下幂函数的习题",
        "幂函数的习题",
        "找幂函数习题",
        "推送幂函数的习题"
    ]
    
    preprocessor = QueryPreprocessor()
    
    for query in test_queries:
        print(f"\n查询: {query}")
        
        # 预处理查询
        result = preprocessor.preprocess(query)
        
        print(f"  清洗后: {result['cleaned_query']}")
        print(f"  关键词: {result['keywords']}")
        print(f"  核心概念: {result['core_concepts']}")
        print(f"  意图: {result['intent']}")
        print(f"  提取的主题: {result['intent'].get('topic', '')}")
        print(f"  资源类型: {result['intent'].get('resource_types', [])}")
        print(f"  指令类型: {result['intent'].get('instruction_type', '')}")


def test_core_theme_extraction():
    """
    测试核心主题提取
    """
    print("\n" + "="*60)
    print("测试: 核心主题提取")
    print("="*60)
    
    test_queries = [
        "帮我找一下幂函数的习题",
        "幂函数的习题",
        "找幂函数习题",
        "推送幂函数的习题"
    ]
    
    retriever = ResourceRetriever()
    
    for query in test_queries:
        core_theme = retriever._extract_core_theme(query)
        print(f"查询: {query} -> 核心主题: '{core_theme}'")


def test_theme_matching():
    """
    测试主题匹配逻辑
    """
    print("\n" + "="*60)
    print("测试: 主题匹配逻辑")
    print("="*60)
    
    test_themes = ["幂函数", "函数的概念", "函数的应用"]
    test_resources = [
        {
            "title": "幂函数练习题",
            "content": "幂函数的定义和性质习题",
            "metadata": {
                "title": "幂函数练习题",
                "source_file": "幂函数练习题.md"
            }
        },
        {
            "title": "函数的概念习题",
            "content": "函数定义和表示法习题",
            "metadata": {
                "title": "函数的概念习题",
                "source_file": "函数的概念习题.md"
            }
        },
        {
            "title": "函数的应用习题",
            "content": "函数在实际问题中的应用",
            "metadata": {
                "title": "函数的应用习题",
                "source_file": "函数的应用习题.md"
            }
        }
    ]
    
    theme_matcher = get_theme_matcher()
    
    for theme in test_themes:
        print(f"\n测试主题: {theme}")
        for resource in test_resources:
            match_result = theme_matcher.match_theme(
                core_theme=theme,
                metadata=resource["metadata"],
                document=resource["content"]
            )
            print(f"  资源: {resource['title']}")
            print(f"    主题匹配: {match_result['is_theme_match']}")
            print(f"    冲突主题: {match_result['is_conflict_theme']}")
            print(f"    加分: {match_result['relevance_boost']:.1%}")
            print(f"    减分: {match_result['relevance_penalty']:.1%}")


def test_resource_retrieval():
    """
    测试资源检索
    """
    print("\n" + "="*60)
    print("测试: 资源检索")
    print("="*60)
    
    test_queries = [
        "幂函数的习题",
        "帮我找一下幂函数的习题"
    ]
    
    retriever = ResourceRetriever()
    
    for query in test_queries:
        print(f"\n测试查询: {query}")
        
        # 检索资源
        results = retriever.retrieve(query, intent='search', resource_types=['习题'])
        
        # 检查习题资源
        exercises = results.get('exercise_resources', [])
        print(f"找到习题资源数量: {len(exercises)}")
        
        if exercises:
            print(f"\n排序结果:")
            for i, exercise in enumerate(exercises[:10], 1):
                title = exercise.get('title', '未知')
                relevance = exercise.get('relevance', 0)
                base_relevance = exercise.get('base_relevance', 0)
                theme_match = exercise.get('theme_match', False)
                
                match_label = "【主题精确匹配】" if theme_match else "【主题相关】"
                print(f"{i}. {match_label} {title} - 相似度: {relevance:.1%} (基础: {base_relevance:.1%})")


def main():
    """
    主测试函数
    """
    print("开始测试幂函数习题检索问题...")
    
    test_query_preprocessing()
    test_core_theme_extraction()
    test_theme_matching()
    test_resource_retrieval()
    
    print("\n" + "="*60)
    print("测试完成！")
    print("="*60)


if __name__ == "__main__":
    main()
