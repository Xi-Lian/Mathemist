"""
检查courseware_849的完整元数据
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

# 获取courseware_849的元数据
results = coll.get(ids=['几何_courseware_849'], include=['metadatas', 'documents'])

if results['metadatas']:
    metadata = results['metadatas'][0]
    print("=" * 80)
    print("courseware_849 完整元数据")
    print("=" * 80)
    for key, value in metadata.items():
        print(f"{key}: {value}")
    
    print("\n" + "=" * 80)
    print("文档内容预览")
    print("=" * 80)
    if results['documents']:
        doc = results['documents'][0]
        print(doc[:500] if len(doc) > 500 else doc)
else:
    print("未找到 courseware_849")
