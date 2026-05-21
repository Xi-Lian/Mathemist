#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path='backend/chroma_db',
    settings=Settings(anonymized_telemetry=False)
)

collection = client.get_collection('math_resources_geometry')

print("=" * 60)
print("查找知识点包含线面角的习题")
print("=" * 60)

# 获取所有文档
results = collection.get(limit=1198, include=["metadatas"])

found_exercises = []
for meta in results['metadatas']:
    resource_type = meta.get('resource_type', '')
    if resource_type != 'exercise':
        continue
    
    analysis_json = meta.get('analysis_json', '')
    if not analysis_json:
        continue
    
    try:
        import json
        analysis = json.loads(analysis_json)
        if isinstance(analysis, dict):
            knowledge_points = analysis.get('知识点', [])
            if isinstance(knowledge_points, list):
                for kp in knowledge_points:
                    if '线面角' in kp:
                        found_exercises.append({
                            'title': meta.get('title', ''),
                            'knowledge_points': knowledge_points,
                            'question': meta.get('题干', '')[:50]
                        })
                        break
    except Exception as e:
        continue

print(f"\n找到 {len(found_exercises)} 条知识点包含线面角的习题")
if found_exercises:
    for i, ex in enumerate(found_exercises):
        print(f"\n{i+1}. {ex['title']}")
        print(f"   知识点: {ex['knowledge_points']}")
        print(f"   题干: {ex['question']}...")

print("\n" + "=" * 60)

# 测试向量搜索
print("\n测试向量搜索'线面角'的结果:")
vector_results = collection.query(
    query_texts=["线面角"],
    n_results=20,
    include=["metadatas"]
)

print(f"\n向量搜索返回 {len(vector_results['metadatas'][0])} 条结果")
print("\n检查前20条结果中是否有包含线面角知识点的:")

count_with_line_angle = 0
for meta in vector_results['metadatas'][0]:
    analysis_json = meta.get('analysis_json', '')
    if analysis_json:
        try:
            import json
            analysis = json.loads(analysis_json)
            kp_list = analysis.get('知识点', [])
            if any('线面角' in kp for kp in kp_list):
                count_with_line_angle += 1
                print(f"✓ {meta.get('title', '')}")
        except:
            pass

print(f"\n前20条结果中包含线面角知识点的有 {count_with_line_angle} 条")

print("\n" + "=" * 60)
print("检查完成")
