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
print("检查几何板块中导入的习题数据")
print("=" * 60)

# 获取集合中的所有文档（前50条）
results = collection.get(limit=50, include=["documents", "metadatas"])

print("文档数量: " + str(len(results['ids'])))

# 检查前10条数据
for i, (doc_id, doc, meta) in enumerate(zip(results['ids'], results['documents'], results['metadatas'])):
    if i >= 10:
        break
    print("")
    print("ID: " + doc_id)
    print("标题: " + str(meta.get('title', '')))
    print("资源类型: " + str(meta.get('resource_type', '')))
    print("文档长度: " + str(len(doc)))
    print("文档预览: " + doc[:100] + "...")
    
    # 检查是否有analysis_json
    if 'analysis_json' in meta:
        print("包含 analysis_json")
        if '面面平行' in meta['analysis_json']:
            print("*** analysis_json 包含 面面平行 ***")

print("")
print("=" * 60)
print("检查完成")
