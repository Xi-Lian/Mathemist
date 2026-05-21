#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

sys.path.insert(0, 'backend')

import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path='backend/chroma_db',
    settings=Settings(
        anonymized_telemetry=False
    )
)

print("=" * 60)
print("检查向量数据库中的习题资源")
print("=" * 60)

collections = client.list_collections()

# 搜索"面面平行"相关的习题
print("\n搜索 '面面平行' 相关资源...")

all_results = []
for collection in collections:
    col = client.get_collection(collection.name)
    try:
        results = col.query(
            query_texts=["面面平行"],
            n_results=20,
            include=["documents", "metadatas"]
        )
        
        docs = results['documents'][0] if results.get('documents') else []
        metas = results['metadatas'][0] if results.get('metadatas') else []
        
        for doc, meta in zip(docs, metas):
            rt = meta.get('resource_type', 'unknown')
            if 'exercise' in rt.lower():
                all_results.append({
                    'collection': collection.name,
                    'title': meta.get('title', '未知标题'),
                    'type': rt,
                    'doc': doc[:150]
                })
    except Exception as e:
        pass

if all_results:
    print(f"找到 {len(all_results)} 条 '面面平行' 相关的习题:")
    for i, result in enumerate(all_results[:10]):
        print(f"\n{i+1}. {result['title']}")
        print(f"   集合: {result['collection']}")
        print(f"   类型: {result['type']}")
        print(f"   预览: {result['doc']}...")
else:
    print("未找到 '面面平行' 相关的习题资源")

# 统计各集合中的习题数量
print("\n" + "=" * 60)
print("各集合习题数量统计:")
print("=" * 60)

for collection in collections:
    col = client.get_collection(collection.name)
    count = col.count()
    
    # 查询 exercise 类型的数量
    try:
        results = col.query(
            query_texts=["test"],
            n_results=count,
            where={"resource_type": {"$in": ["exercise", "习题", "题目"]}},
            include=["metadatas"]
        )
        meta_count = len(results['metadatas'][0]) if results.get('metadatas') else 0
    except Exception as e:
        meta_count = 0
    
    print(f"{collection.name}: 总数={count}, 习题={meta_count}")

print("\n" + "=" * 60)
print("检查完成")
print("=" * 60)
