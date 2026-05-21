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
print("检查线面角习题的文档内容")
print("=" * 60)

results = collection.get(limit=1198, include=["metadatas", "documents"])

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
                            'document': doc,
                            'has_line_angle_in_doc': '线面角' in doc
                        })
                        break
    except Exception as e:
        continue

print(f"\n找到 {len(found_exercises)} 条知识点包含线面角的习题")
if found_exercises:
    for i, ex in enumerate(found_exercises):
        print(f"\n{i+1}. {ex['title']}")
        print(f"   知识点: {ex['knowledge_points']}")
        print(f"   文档内容包含'线面角': {'是' if ex['has_line_angle_in_doc'] else '否'}")
        print(f"   文档长度: {len(ex['document'])} 字符")
        
        # 检查文档内容的前100字符（清理特殊字符）
        try:
            clean_doc = ex['document'].replace('\u27e8', '<').replace('\u27e9', '>')
            print(f"   文档内容预览: {clean_doc[:100]}...")
        except:
            print(f"   文档内容预览: 无法显示")

print("\n" + "=" * 60)
print("检查完成")
