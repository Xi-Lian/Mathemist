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
print("检查数据库中 '面面平行' 相关习题")
print("=" * 60)

# 直接搜索知识点包含"面面平行"的文档
results = collection.query(
    query_texts=["面面平行的判定", "面面平行的性质"],
    n_results=15,
    include=["documents", "metadatas"]
)

all_docs = []
all_metas = []

if results.get('documents'):
    for doc_list in results['documents']:
        all_docs.extend(doc_list)
if results.get('metadatas'):
    for meta_list in results['metadatas']:
        all_metas.extend(meta_list)

seen = set()
unique_results = []
for doc, meta in zip(all_docs, all_metas):
    key = meta.get('title', '') + str(meta.get('题干', '')[:30])
    if key not in seen:
        seen.add(key)
        unique_results.append((doc, meta))

if unique_results:
    print(f"找到 {len(unique_results)} 条相关习题:")
    for i, (doc, meta) in enumerate(unique_results[:10]):
        print(f"\n{i+1}. {meta.get('title', '')}")
        
        # 检查是否有analysis_json字段
        analysis_json = meta.get('analysis_json', '')
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    print(f"   知识点: {analysis.get('知识点', [])}")
                    print(f"   题型: {analysis.get('题型', '')}")
                    print(f"   核心考点: {analysis.get('核心考点', '')}")
            except:
                pass
        
        # 显示题干
        question = meta.get('题干', '')[:100] if meta.get('题干') else doc[:100]
        print(f"   题干预览: {question}...")
        print(f"   资源类型: {meta.get('resource_type', '')}")
        
else:
    print("未找到相关习题")

print("\n" + "=" * 60)
print("检查完成")
