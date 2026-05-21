"""
检查所有ChromaDB集合
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()

collections = client.list_collections()

print("=" * 80)
print("所有ChromaDB集合")
print("=" * 80)

for col in collections:
    print(f"\n集合名称: {col.name}")
    print(f"  文档数量: {col.count()}")
