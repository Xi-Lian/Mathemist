#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
调试检索流程，找出为什么只有1条结果
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_retrieval_flow():
    """调试三角恒等变换习题的检索流程"""
    print("=" * 80)
    print("调试检索流程 - 三角恒等变换习题")
    print("=" * 80)
    
    try:
        from app.core.model_config import model_config
        
        # 获取向量数据库客户端
        vector_db = model_config.get_chroma_client()
        
        # 获取函数板块集合
        collection = vector_db.get_collection('math_resources_function')
        
        # 步骤1: 向量检索
        print("\n【步骤1: 向量检索】")
        print("-" * 60)
        results = collection.query(
            query_texts=['三角恒等变换'],
            n_results=20,
            where={"resource_type": "exercise"},
            include=['documents', 'metadatas', 'distances']
        )
        
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        distances = results['distances'][0]
        
        print(f"向量检索返回: {len(docs)} 条结果")
        print()
        
        # 统计知识点分布
        knowledge_counts = {}
        for meta in metas:
            knowledge = meta.get('知识点', '无')
            knowledge_counts[knowledge] = knowledge_counts.get(knowledge, 0) + 1
        
        print("知识点分布:")
        for knowledge, count in sorted(knowledge_counts.items(), key=lambda x: -x[1]):
            print(f"  {knowledge}: {count}条")
        
        # 步骤2: 检查每条资源的详细信息
        print("\n【步骤2: 检查每条资源的详细信息】")
        print("-" * 60)
        
        for i, (doc, meta, dist) in enumerate(zip(docs, metas, distances)):
            title = meta.get('title', '空')
            question = meta.get('题干', '').strip()
            knowledge = meta.get('知识点', '空')
            score = max(0, 1 - dist)  # 将距离转换为分数
            
            print(f"\n资源 {i+1} (分数: {score:.4f}):")
            print(f"  标题: {title}")
            print(f"  知识点: {knowledge}")
            print(f"  题干长度: {len(question)}")
            if question:
                print(f"  题干预览: {question[:100]}...")
            
            # 检查是否包含三角恒等变换相关内容
            has_triangle = False
            if '三角' in knowledge or '三角' in title or '三角' in question:
                has_triangle = True
            if '恒等变换' in knowledge or '恒等变换' in title or '恒等变换' in question:
                has_triangle = True
            if '诱导公式' in knowledge or '诱导公式' in title or '诱导公式' in question:
                has_triangle = True
            if '二倍角' in knowledge or '二倍角' in title or '二倍角' in question:
                has_triangle = True
            
            print(f"  包含三角相关内容: {'是' if has_triangle else '否'}")
            
            # 预测是否会被过滤
            if score < 0.3:
                print(f"  ⚠️ 可能被过滤: 相关性分数过低 ({score:.4f})")
            if knowledge == '无' and score < 0.5:
                print(f"  ⚠️ 可能被过滤: 无知识点标签且相关性不高")
        
        # 步骤3: 检查知识图谱扩展
        print("\n【步骤3: 检查知识图谱扩展】")
        print("-" * 60)
        try:
            from app.core.knowledge_graph import KnowledgeGraph
            kg = KnowledgeGraph()
            
            related_concepts = kg.get_related_nodes('三角恒等变换')
            print(f"与'三角恒等变换'相关的概念: {related_concepts}")
            
            expanded_query = kg.expand_query('三角恒等变换')
            print(f"扩展查询词: {expanded_query}")
        except Exception as e:
            print(f"知识图谱查询失败: {e}")
        
        # 步骤4: 检查知识库中的三角恒等变换相关习题总数
        print("\n【步骤4: 检查三角恒等变换相关习题总数】")
        print("-" * 60)
        
        # 尝试使用不同的查询条件
        all_results = collection.get(
            where={"resource_type": "exercise"},
            include=['metadatas']
        )
        
        metas_all = all_results['metadatas']
        triangle_exercises = []
        
        for meta in metas_all:
            knowledge = meta.get('知识点', '')
            title = meta.get('title', '')
            question = meta.get('题干', '')
            
            # 检查是否与三角恒等变换相关
            if any(keyword in knowledge for keyword in ['三角恒等变换', '诱导公式', '二倍角', '三角']):
                triangle_exercises.append(meta)
            elif any(keyword in title for keyword in ['三角恒等变换', '诱导公式', '二倍角', '三角']):
                triangle_exercises.append(meta)
            elif any(keyword in question for keyword in ['三角恒等变换', '诱导公式', '二倍角', '三角']):
                triangle_exercises.append(meta)
        
        print(f"知识库中三角相关习题总数: {len(triangle_exercises)}")
        
        # 统计这些习题的知识点分布
        print("\n三角相关习题的知识点分布:")
        kg_counts = {}
        for meta in triangle_exercises:
            knowledge = meta.get('知识点', '无')
            kg_counts[knowledge] = kg_counts.get(knowledge, 0) + 1
        
        for knowledge, count in sorted(kg_counts.items(), key=lambda x: -x[1])[:10]:
            print(f"  {knowledge}: {count}条")
        
    except Exception as e:
        print(f"调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_retrieval_flow()
    print("\n" + "=" * 80)
    print("调试完成")
    print("=" * 80)
