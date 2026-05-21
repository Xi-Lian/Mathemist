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
print("验证面面平行习题是否已导入数据库")
print("=" * 60)

test_ids = [
    "exercise_1094_19317",
    "exercise_1097_19317",
    "exercise_1098_19317",
    "exercise_1106_22558"
]

found_count = 0
for exercise_id in test_ids:
    try:
        results = collection.get(ids=[exercise_id], include=["metadatas", "documents"])
        if results['ids']:
            found_count += 1
            meta = results['metadatas'][0]
            doc = results['documents'][0] if results.get('documents') else ''
            print("")
            print("找到 " + exercise_id)
            print("   标题: " + str(meta.get('title', '')))
            print("   资源类型: " + str(meta.get('resource_type', '')))
            
            analysis_json = meta.get('analysis_json', '')
            if analysis_json:
                import json
                try:
                    analysis = json.loads(analysis_json)
                    if isinstance(analysis, dict):
                        print("   知识点: " + str(analysis.get('知识点', [])))
                except:
                    pass
        else:
            print("")
            print("未找到 " + exercise_id)
    except Exception as e:
        print("")
        print("查询 " + exercise_id + " 时出错: " + str(e))

print("")
print("共验证 " + str(len(test_ids)) + " 个ID，找到 " + str(found_count) + " 个")

print("")
print("=" * 60)
print("搜索所有包含面面平行的文档...")

results = collection.query(
    query_texts=["面面平行"],
    n_results=30,
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

parallel_plane_results = []
for doc, meta in zip(all_docs, all_metas):
    has_parallel = False
    if '面面平行' in doc:
        has_parallel = True
    if 'analysis_json' in meta and '面面平行' in meta['analysis_json']:
        has_parallel = True
    if has_parallel:
        parallel_plane_results.append((doc, meta))

print("找到 " + str(len(parallel_plane_results)) + " 条真正包含面面平行的文档")
for i, (doc, meta) in enumerate(parallel_plane_results[:5]):
    print("")
    print(str(i+1) + ". " + str(meta.get('title', '')))
    print("   资源类型: " + str(meta.get('resource_type', '')))
    if 'analysis_json' in meta and '面面平行' in meta['analysis_json']:
        print("   analysis_json包含面面平行")
    if '面面平行' in doc:
        print("   文档内容包含面面平行")

print("")
print("=" * 60)
print("验证完成")
