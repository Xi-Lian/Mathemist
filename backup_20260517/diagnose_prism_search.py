"""
诊断棱柱课件检索问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.service import ResourceRetriever

def diagnose_prism_search():
    """诊断棱柱课件检索"""
    
    print("=" * 80)
    print("诊断棱柱课件检索问题")
    print("=" * 80)
    
    retriever = ResourceRetriever()
    
    # 模拟用户查询
    query = "我想要棱柱的练习课课件"
    
    print(f"\n用户查询: {query}")
    print("\n开始检索...\n")
    
    # 执行检索
    result = retriever.retrieve(
        query=query,
        intent="search",
        resource_types=["课件"]
    )
    
    # 分析结果
    print("\n" + "=" * 80)
    print("检索结果分析")
    print("=" * 80)
    
    courseware_resources = result.get('courseware_resources', [])
    print(f"\n找到课件资源数量: {len(courseware_resources)}")
    
    if courseware_resources:
        print("\n返回的课件列表:")
        for i, resource in enumerate(courseware_resources, 1):
            print(f"\n{i}. {resource.get('title', '未知')}")
            print(f"   文件名: {resource.get('filename', '未知')}")
            print(f"   教学用途: {resource.get('teaching_use', '未知')}")
            print(f"   相关性: {resource.get('relevance', 0):.3f}")
            print(f"   知识点: {resource.get('knowledge_tags', '未知')}")
    else:
        print("\n❌ 没有找到任何课件资源！")
    
    # 检查所有资源类型
    print("\n" + "=" * 80)
    print("所有资源类型统计")
    print("=" * 80)
    for key, value in result.items():
        if isinstance(value, list):
            print(f"{key}: {len(value)} 条")
    
    print("\n" + "=" * 80)
    print("诊断完成")
    print("=" * 80)


if __name__ == '__main__':
    try:
        diagnose_prism_search()
    except Exception as e:
        print(f"\n❌ 诊断失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
