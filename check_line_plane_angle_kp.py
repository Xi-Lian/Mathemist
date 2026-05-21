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
print("检查几何板块中知识点包含线面角的习题")
print("=" * 60)

results = collection.get(limit=1198, include=["documents", "metadatas"])

found_exercises = []
for doc, meta in zip(results['documents'], results['metadatas']):
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
    except:
        continue

print(f"找到 {len(found_exercises)} 条知识点包含线面角的习题")
if found_exercises:
    for i, ex in enumerate(found_exercises[:5]):
        print(f"\n{i+1}. {ex['title']}")
        print(f"   知识点: {ex['knowledge_points']}")
        print(f"   题干: {ex['question']}...")

print("\n" + "=" * 60)
print("检查完成")
