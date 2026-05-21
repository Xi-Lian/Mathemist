"""
诊断棱柱练习课课件检索失败问题
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval.service import ResourceRetriever

def diagnose_prism_practice_search():
    """诊断棱柱练习课课件检索"""
    
    print("=" * 80)
    print("诊断棱柱练习课课件检索失败问题")
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
    
    if len(courseware_resources) == 0:
        print("\n没有找到任何课件资源！")
        print("\n可能原因:")
        print("  1. 向量检索阶段没有召回任何资源")
        print("  2. 评估器过滤掉了所有资源")
        print("  3. 板块选择错误")
    else:
        print(f"\n找到 {len(courseware_resources)} 个课件:")
        for i, resource in enumerate(courseware_resources[:5], 1):
            print(f"\n{i}. {resource.get('title', 'N/A')}")
            print(f"   适配说明: {resource.get('adaptation_note', 'N/A')}")
            print(f"   得分: {resource.get('score', 'N/A')}")
            print(f"   教学用途: {resource.get('teaching_use', 'N/A')}")
    
    # 检查原始检索结果（如果有调试信息）
    print("\n" + "=" * 80)
    print("建议下一步")
    print("=" * 80)
    print("\n如果结果为空，请检查:")
    print("  1. 查看后端日志中的评估器评分详情")
    print("  2. 检查阈值是否设置过高")
    print("  3. 确认向量数据库中有相关资源")

if __name__ == "__main__":
    diagnose_prism_practice_search()
