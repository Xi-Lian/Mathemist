#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.simple_exercise_retrieval import simple_exercise_retrieval
from app.core.vector_database_builder import VectorDatabaseBuilder

print("=" * 70)
print("最终测试：搜索'线面角'习题")
print("=" * 70)

builder = VectorDatabaseBuilder('learning_resource')
vector_db = builder.get_chroma_client()

query = "线面角"
core_theme = "线面角"

print(f"\n执行检索...")
print(f"查询: '{query}'")
print(f"核心主题: '{core_theme}'")

results = simple_exercise_retrieval(
    query=query,
    core_theme=core_theme,
    vector_db=vector_db,
    n_results=5,
    resource_types=["exercise"]
)

print(f"\n检索结果数量: {len(results)}")

if results:
    print("\n前5条结果:")
    print("-" * 70)
    for i, result in enumerate(results[:5], 1):
        meta = result.get('metadata', {})
        title = meta.get('title', '')
        score = result.get('score', 0)
        
        print(f"\n{i}. {title}")
        print(f"   分数: {score:.4f}")
        
        analysis_json = meta.get('analysis_json', '')
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    kp_list = analysis.get('知识点', [])
                    print(f"   知识点: {kp_list}")
                    
                    has_line_angle = any('线面角' in kp for kp in kp_list)
                    print(f"   ✅ 包含'线面角'知识点" if has_line_angle else "   ❌ 不包含'线面角'知识点")
            except Exception as e:
                print(f"   解析失败: {e}")
else:
    print("\n❌ 未找到任何结果！")
    print("\n检查数据库中是否存在线面角习题...")

    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path='backend/chroma_db',
        settings=Settings(anonymized_telemetry=False)
    )

    collection = client.get_collection('math_resources_geometry')
    count = collection.count()
    print(f"几何集合总文档数: {count}")

    all_docs = collection.get(limit=1198, include=["metadatas"])

    line_angle_count = 0
    for meta in all_docs['metadatas']:
        analysis_json = meta.get('analysis_json', '')
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                kp_list = analysis.get('知识点', [])
                if any('线面角' in kp for kp in kp_list):
                    line_angle_count += 1
                    if line_angle_count <= 3:
                        print(f"\n  [{line_angle_count}] {meta.get('title', '')}")
                        print(f"      知识点: {kp_list}")
            except:
                pass

    print(f"\n数据库中包含'线面角'知识点的习题总数: {line_angle_count}")

print("\n" + "=" * 70)
print("测试完成")
