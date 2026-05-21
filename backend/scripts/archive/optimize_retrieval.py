#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_knowledge_graph():
    print("=" * 60)
    print("1. 测试知识图谱")
    print("=" * 60)
    
    try:
        from app.core.knowledge_graph import KnowledgeGraph
        
        kg = KnowledgeGraph()
        print("知识图谱加载成功")
        print("   节点数:", kg.get_node_count())
        print("   边数:", kg.get_edge_count())
        
        related = kg.get_related_nodes('三角恒等变换')
        print("\n与'三角恒等变换'相关的概念:")
        for i, concept in enumerate(related[:8]):
            print("   %d. %s" % (i+1, concept))
        
        expanded = kg.expand_query('三角恒等变换')
        print("\n扩展查询:", expanded)
        
        return kg
        
    except Exception as e:
        print("知识图谱测试失败:", str(e)[:100])
        import traceback
        traceback.print_exc()
        return None

def test_retrieval_with_kg():
    print("\n" + "=" * 60)
    print("2. 测试知识图谱增强检索")
    print("=" * 60)
    
    try:
        from app.core.knowledge_graph import KnowledgeGraph
        from app.core.retrieval.resource_retriever import ResourceRetriever
        
        kg = KnowledgeGraph()
        retriever = ResourceRetriever()
        
        query = '三角函数恒等变换'
        
        expanded_query = kg.expand_query(query)
        print("原始查询:", query)
        print("扩展查询:", expanded_query)
        
        results = retriever.retrieve(expanded_query, resource_types=['exercise'], n_results=5)
        
        docs = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        print("\n检索结果数:", len(docs))
        
        if docs:
            print("\n前5条结果:")
            for i, doc in enumerate(docs[:5]):
                meta = metadatas[i] if metadatas else {}
                title = meta.get('title', '未知')
                knowledge = meta.get('知识点', '未知')
                
                print("\n%d. 标题: %s" % (i+1, title))
                print("   知识点: %s" % knowledge)
                
                kg_score = kg.validate_concept_match(query, doc)
                print("   KG匹配度: %.2f" % kg_score)
                
                print("   内容预览: %s..." % doc[:80])
        
    except Exception as e:
        print("检索测试失败:", str(e)[:100])
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    kg = test_knowledge_graph()
    if kg:
        test_retrieval_with_kg()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)