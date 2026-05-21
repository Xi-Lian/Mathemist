#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.simple_exercise_retrieval import simple_exercise_retrieval
from app.core.vector_database_builder import VectorDatabaseBuilder

print("=" * 60)
print("测试面面平行搜索功能")
print("=" * 60)

# 获取向量数据库客户端
builder = VectorDatabaseBuilder('learning_resource')
vector_db = builder.get_chroma_client()

# 测试搜索"面面平行"
print("\n测试搜索: 面面平行")
results = simple_exercise_retrieval(
    query="面面平行",
    core_theme="面面平行",
    vector_db=vector_db,
    n_results=10,
    resource_types=["exercise"]
)

print(f"搜索结果数量: {len(results)}")

if results:
    for i, result in enumerate(results[:5]):
        meta = result.get('metadata', {})
        title = meta.get('title', '')
        question = meta.get('题干', '')[:80] if meta.get('题干') else ''
        analysis_json = meta.get('analysis_json', '')
        
        print(f"\n{i+1}. {title}")
        if question:
            print(f"   题干: {question}...")
        
        if analysis_json:
            import json
            try:
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    print(f"   知识点: {analysis.get('知识点', [])}")
                    print(f"   题型: {analysis.get('题型', '')}")
            except:
                pass
        
        print(f"   分数: {result.get('score', 0):.3f}")

print("\n" + "=" * 60)
print("测试完成")
