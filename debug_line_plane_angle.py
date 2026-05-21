#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.simple_exercise_retrieval import simple_exercise_retrieval
from app.core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder('learning_resource')
vector_db = builder.get_chroma_client()

print("=" * 60)
print("调试线面角检索")
print("=" * 60)

results = simple_exercise_retrieval(
    query="线面角",
    core_theme="线面角",
    vector_db=vector_db,
    n_results=20,
    resource_types=["exercise"]
)

print(f"\n返回结果数量: {len(results)}")
print("\n详细分析每个结果:")

for i, result in enumerate(results):
    meta = result.get('metadata', {})
    title = meta.get('title', '')
    score = result.get('score', 0)
    distance = result.get('distance', 0)
    
    # 检查知识点
    has_kp_match = False
    kp_list = []
    analysis_json = meta.get('analysis_json', '')
    if analysis_json:
        try:
            import json
            analysis = json.loads(analysis_json)
            if isinstance(analysis, dict):
                kp_list = analysis.get('知识点', [])
                if isinstance(kp_list, list):
                    for kp in kp_list:
                        if '线面角' in kp:
                            has_kp_match = True
                            break
        except:
            pass
    
    print(f"\n{i+1}. {title}")
    print(f"   分数: {score:.4f}, 距离: {distance:.4f}")
    print(f"   知识点包含线面角: {'是' if has_kp_match else '否'}")
    if kp_list:
        print(f"   知识点列表: {kp_list}")

print("\n" + "=" * 60)
print("调试完成")
