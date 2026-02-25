#!/usr/bin/env python3
"""
测试幂函数习题搜索结果（详细版）
"""

from app.core.resource_retriever import retrieve_resources

if __name__ == "__main__":
    print("=== 测试幂函数习题搜索（详细版）===")
    query = "幂函数的习题"
    result = retrieve_resources(query)
    
    print(f"\n搜索查询: {query}")
    print(f"习题资源数量: {len(result['exercise_resources'])}")
    
    # 打印所有习题资源，特别关注幂函数相关的
    print("\n所有习题资源:")
    power_function_exercises = []
    for i, res in enumerate(result['exercise_resources']):
        is_power_function = '幂函数' in res['source'] or '3-3' in res['source']
        if is_power_function:
            power_function_exercises.append((i, res))
            print(f"\n{i+1}. {res['source']} - 相似度: {res['relevance']:.1%}, 主题匹配: {res['theme_match']}")
            if 'theme_boost' in res:
                print(f"   主题匹配加分: {res['theme_boost']:.1%}")
            if 'base_relevance' in res:
                print(f"   基础相似度: {res['base_relevance']:.1%}")
            if 'theme_match' in res:
                print(f"   主题匹配: {res['theme_match']}")
    
    if not power_function_exercises:
        print("\n❌ 没有找到幂函数相关的习题资源")
    else:
        print(f"\n✅ 找到 {len(power_function_exercises)} 个幂函数相关的习题资源")
        print("\n幂函数习题资源在结果中的位置:")
        for i, res in power_function_exercises:
            print(f"   第 {i+1} 位: {res['source']} - 相似度: {res['relevance']:.1%}")
