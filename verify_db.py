#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

# 确保 backend 在路径中
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
sys.path.insert(0, backend_path)

import chromadb
from chromadb.config import Settings

print("=" * 60)
print("验证向量数据库")
print("=" * 60)

# 获取数据库路径
db_path = os.path.join(backend_path, 'chroma_db')
print(f"数据库路径: {db_path}")

# 连接到数据库
client = chromadb.PersistentClient(
    path=db_path,
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# 获取所有集合
collections = client.list_collections()
print(f"\n找到 {len(collections)} 个集合:")

total_records = 0

for collection in collections:
    col = client.get_collection(collection.name)
    count = col.count()
    total_records += count
    print(f"  - {collection.name}: {count} 条记录")
    
    # 获取前几个记录看看
    if count > 0:
        sample = col.peek(limit=1)
        if sample['metadatas']:
            first_meta = sample['metadatas'][0]
            print(f"    示例资源类型: {first_meta.get('resource_type', 'unknown')}")

print(f"\n总计: {total_records} 条记录")
print("\n" + "=" * 60)
print("数据库验证完成！")
print("=" * 60)
