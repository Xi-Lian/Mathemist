#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟检索"找一下分段函数单调性的题"，检查那两条目标习题是否被召回
"""
import sys
sys.path.insert(0, 'backend')

from app.core.model_config import model_config

def simulate_retrieval():
    """模拟检索过程"""
    db = model_config.get_chroma_client()
    col = db.get_or_create_collection('math_resources_function')
    
    # 获取embedding模型
    emb_model = model_config.get_embedding_model()
    
    # 查询文本
    query_text = "找一下分段函数单调性的题"
    
    print(f"查询文本: {query_text}")
    print("="*80)
    
    # 生成查询向量
    query_vec = emb_model.encode([query_text], normalize_embeddings=True)
    
    # 执行向量检索，返回前20条结果
    results = col.query(
        query_embeddings=query_vec.tolist(),
        n_results=20,
        where={"resource_type": "exercise"},
        include=['metadatas', 'documents', 'distances']
    )
    
    print(f"\n向量检索返回 {len(results['ids'][0])} 条结果")
    print("="*80)
    
    # 检查目标习题是否在结果中
    target_ids = ['函数_exercise_205', '函数_exercise_210']
    found_targets = []
    
    for i, (id, meta, doc, distance) in enumerate(zip(
        results['ids'][0],
        results['metadatas'][0],
        results['documents'][0],
        results['distances'][0]
    )):
        similarity = 1 - distance  # ChromaDB使用余弦距离，相似度 = 1 - distance
        
        title = meta.get('title', '')
        knowledge_tags = meta.get('知识点标签', '') or meta.get('知识点', '')
        source_file = meta.get('source_file', '')
        
        is_target = id in target_ids
        marker = "[TARGET]" if is_target else ""
        
        print(f"\n[{i+1}] {marker} ID: {id}")
        print(f"    Title: {title}")
        print(f"    Source: {source_file}")
        print(f"    知识点标签: {knowledge_tags}")
        print(f"    Distance: {distance:.4f}, Similarity: {similarity:.4f}")
        print(f"    Document预览: {doc[:100]}...")
        
        if is_target:
            found_targets.append((id, similarity))
    
    print("\n" + "="*80)
    print(f"目标习题检查结果:")
    for target_id in target_ids:
        found = any(id == target_id for id, _ in found_targets)
        if found:
            sim = next(sim for id, sim in found_targets if id == target_id)
            print(f"  [OK] {target_id} - 已找到，相似度: {sim:.4f}")
        else:
            print(f"  [NO] {target_id} - 未找到（不在前20条结果中）")

if __name__ == '__main__':
    simulate_retrieval()
