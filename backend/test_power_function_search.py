#!/usr/bin/env python3
"""
测试幂函数习题搜索结果
"""

from app.core.resource_retriever import retrieve_resources

if __name__ == "__main__":
    print("=== 测试幂函数习题搜索 ===")
    query = "幂函数的习题"
    result = retrieve_resources(query)
    
    print(f"\n搜索查询: {query}")
    print(f"习题资源数量: {len(result['exercise_resources'])}")
    
    print("\n前10个习题资源:")
    for i, res in enumerate(result['exercise_resources'][:10]):
        print(f"{i+1}. {res['source']} - 相似度: {res['relevance']:.1%}, 主题匹配: {res['theme_match']}")
        if 'theme_boost' in res:
            print(f"   主题匹配加分: {res['theme_boost']:.1%}")
        if 'base_relevance' in res:
            print(f"   基础相似度: {res['base_relevance']:.1%}")
