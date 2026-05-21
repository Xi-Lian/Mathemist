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
print("搜索 '面面平行' 相关习题")
print("=" * 60)

collection = client.get_collection('math_resources_geometry')
print("\n正在几何板块中搜索...")

results = collection.query(
    query_texts=["面面平行", "平面与平面平行", "面面平行性质", "面面平行判定"],
    n_results=20,
    where={"resource_type": "exercise"},
    include=["documents", "metadatas"]
)

# ChromaDB返回的是数组的数组
all_docs = []
all_metas = []

if results.get('documents'):
    for doc_list in results['documents']:
        all_docs.extend(doc_list)
if results.get('metadatas'):
    for meta_list in results['metadatas']:
        all_metas.extend(meta_list)

if all_docs:
    print(f"找到 {len(all_docs)} 条相关习题:")
    
    # 去重
    seen = set()
    unique_results = []
    for doc, meta in zip(all_docs, all_metas):
        key = (meta.get('title', ''), meta.get('题干', '')[:50])
        if key not in seen:
            seen.add(key)
            unique_results.append((doc, meta))
    
    print(f"去重后: {len(unique_results)} 条")
    
    for i, (doc, meta) in enumerate(unique_results[:10]):
        title = meta.get('title', '未知标题')
        question = meta.get('题干', '')[:100] if meta.get('题干') else doc[:100]
        analysis_json = meta.get('analysis_json', '')
        
        has_parallel = False
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    knowledge_points = analysis.get('知识点', [])
                    if any('面面平行' in kp for kp in knowledge_points):
                        has_parallel = True
            except:
                pass
        
        if not has_parallel:
            if '面面平行' in doc or '平面平行' in doc or 'α∥β' in doc or 'α平行β' in doc:
                has_parallel = True
        
        print(f"\n{i+1}. {title}")
        print(f"   题干预览: {question}...")
        if has_parallel:
            print(f"   ✅ 包含面面平行知识点")
        
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    print(f"   知识点: {analysis.get('知识点', [])}")
                    print(f"   题型: {analysis.get('题型', '')}")
                    core = analysis.get('核心考点', '')[:50]
                    print(f"   核心考点: {core}...")
            except:
                pass
    
else:
    print("未找到相关习题")

print("\n" + "=" * 60)
print("搜索完成")
print("=" * 60)
