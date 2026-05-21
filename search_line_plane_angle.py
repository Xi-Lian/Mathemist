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

print("=" * 60)
print("搜索数据库中所有包含线面角的文档")
print("=" * 60)

collections = client.list_collections()

found_count = 0
for col_name in [c.name for c in collections]:
    collection = client.get_collection(col_name)
    count = collection.count()
    results = collection.get(limit=count, include=["documents", "metadatas"])
    
    for doc, meta in zip(results['documents'], results['metadatas']):
        has_angle = False
        if '线面角' in doc or '线面夹角' in doc:
            has_angle = True
        if 'analysis_json' in meta and ('线面角' in meta['analysis_json'] or '线面夹角' in meta['analysis_json']):
            has_angle = True
        
        if has_angle:
            found_count += 1
            title = meta.get('title', '')
            rt = meta.get('resource_type', '')
            print(f"找到: {title} ({rt})")

print(f"\n共找到 {found_count} 条线面角相关文档")

# 检查分析文件
print("\n" + "=" * 60)
print("检查分析文件中是否有线面角相关内容...")

analysis_dir = 'learning_resource/exercise_analysis'
angle_files = []
for filename in os.listdir(analysis_dir):
    if filename.endswith('.json'):
        filepath = os.path.join(analysis_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                if '线面角' in content:
                    angle_files.append(filename)
        except:
            pass

print(f"分析文件中找到 {len(angle_files)} 个包含线面角的文件")
if angle_files:
    print("示例文件:", angle_files[:3])

print("\n" + "=" * 60)
print("检查完成")
