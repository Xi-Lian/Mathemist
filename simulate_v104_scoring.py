#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模拟V104.0评分逻辑，比较两条目标习题的得分
"""
import sys
sys.path.insert(0, 'backend')
import re
from app.core.model_config import model_config

def simulate_scoring():
    """模拟评分"""
    
    db = model_config.get_chroma_client()
    col = db.get_or_create_collection('math_resources_function')
    
    # 获取embedding模型
    emb_model = model_config.get_embedding_model()
    
    # 查询文本
    query = "找一下分段函数单调性的题"
    core_theme = "分段函数单调性, 分段函数, 函数的单调性, 函数单调性"
    
    print(f"查询: {query}")
    print(f"Core Theme: {core_theme}")
    print("="*80)
    
    # 生成查询向量
    query_vec = emb_model.encode([query], normalize_embeddings=True)
    
    target_ids = ['函数_exercise_205', '函数_exercise_210']
    
    for target_id in target_ids:
        # 先获取metadata和document
        result = col.get(ids=[target_id], include=['metadatas', 'documents'])
        if result['metadatas']:
            meta = result['metadatas'][0]
            doc = result['documents'][0] if result['documents'] else ''
            
            # 再查询获取distance
            query_result = col.query(
                query_embeddings=query_vec.tolist(),
                n_results=1,
                where={'id': target_id},
                include=['distances']
            )
            distance = query_result['distances'][0][0] if query_result['distances'] and query_result['distances'][0] else 1.0
            
            print(f"\n{'='*80}")
            print(f"{target_id}:")
            print(f"{'='*80}")
            
            # 1. 向量相似度评分
            similarity = 1 - distance
            vector_score = similarity * 0.4
            print(f"\n1. 向量相似度: {similarity:.4f}")
            print(f"   贡献分数: {similarity:.4f} × 0.4 = {vector_score:.4f}")
            
            # 2. 知识点标签匹配
            knowledge_points_str = meta.get('知识点标签', '') or meta.get('知识点', '')
            knowledge_points = [kp.strip() for kp in knowledge_points_str.split(';') if kp.strip()]
            print(f"\n2. 知识点标签: {knowledge_points}")
            
            # V104.0: 知识点精确匹配加分
            query_keywords = [kw.strip() for kw in re.findall(r'[\u4e00-\u9fa5]{2,}', query) if len(kw.strip()) >= 2]
            print(f"   查询关键词: {query_keywords}")
            
            exact_kp_bonus = 0.0
            for kw in query_keywords:
                if any(kw == kp or kw in kp for kp in knowledge_points):
                    exact_kp_bonus = 0.5
                    print(f"   ✅ 知识点精确匹配: '{kw}' in {knowledge_points}, +0.5")
                    break
            
            print(f"   V104.0加分: +{exact_kp_bonus}")
            
            # 其他匹配（简化版）
            other_score = 0.4  # 假设知识点匹配得0.4分
            print(f"   其他匹配加分: +{other_score}")
            
            # 总分
            total_score = vector_score + exact_kp_bonus + other_score
            print(f"\n{'='*80}")
            print(f"总分: {vector_score:.4f} + {exact_kp_bonus:.1f} + {other_score:.1f} = {total_score:.4f}")
            print(f"{'='*80}")
            
            # 其他可能影响的因素
            print(f"\n其他字段:")
            print(f"  Title: {meta.get('title', '')}")
            print(f"  Source: {meta.get('source_file', '')}")
            print(f"  难度: {meta.get('难度（1-5）', '') or meta.get('难度', '')}")
            print(f"  适用场景: {meta.get('适用场景', '')}")
            analysis = meta.get('analysis', {})
            if isinstance(analysis, dict):
                print(f"  核心考点: {analysis.get('核心考点', '')[:50]}...")

if __name__ == '__main__':
    simulate_scoring()
