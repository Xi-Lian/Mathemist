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
print("搜索数据库中所有包含面面平行的文档")
print("=" * 60)

collections = client.list_collections()

for col_name in [c.name for c in collections]:
    print("")
    print("检查集合: " + col_name)
    
    collection = client.get_collection(col_name)
    count = collection.count()
    print("  文档总数: " + str(count))
    
    # 获取所有文档
    results = collection.get(limit=count, include=["documents", "metadatas"])
    
    found = 0
    for doc, meta in zip(results['documents'], results['metadatas']):
        if '面面平行' in doc:
            found += 1
        if 'analysis_json' in meta and '面面平行' in meta['analysis_json']:
            found += 1
    
    print("  包含面面平行的文档数: " + str(found))

print("")
print("=" * 60)
print("搜索完成")
