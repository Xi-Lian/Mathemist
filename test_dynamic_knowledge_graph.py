#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.simple_exercise_retrieval import _get_collection_name_by_theme, _get_collection_by_knowledge_graph
from app.core.knowledge_graph import KnowledgeGraph

print("=" * 60)
print("测试动态知识图谱主题识别")
print("=" * 60)

# 测试知识图谱
kg = KnowledgeGraph()
print(f"知识图谱节点数: {kg.get_node_count()}")
print(f"知识图谱边数: {kg.get_edge_count()}")

# 测试动态识别
test_queries = [
    "线面角",
    "二面角",
    "面面平行",
    "空间向量",
    "概率",
    "三角函数",
    "复数",
    "对数函数",
    "圆锥曲线",
    "立体几何"
]

print("\n测试动态主题识别:")
print("-" * 60)

for query in test_queries:
    collection = _get_collection_by_knowledge_graph(query)
    fallback_collection = _get_collection_name_by_theme(query)
    
    print(f"\n查询: '{query}'")
    print(f"  知识图谱识别: {collection if collection else '未识别'}")
    print(f"  最终路由: {fallback_collection}")
    
    # 显示知识图谱匹配详情
    try:
        match_result = kg.universal_match([query])
        if match_result['matched_nodes']:
            print(f"  匹配节点数: {len(match_result['matched_nodes'])}")
            print(f"  匹配标签: {', '.join(match_result['labels'][:5])}")
    except:
        pass

print("\n" + "=" * 60)
print("测试完成")
