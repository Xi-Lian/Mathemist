import sys, os
sys.path.insert(0, 'backend')
from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')
results = coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])

coursewares = [m for m in results['metadatas'] if '棱柱' in m.get('文件名', '') or ('课时1' in m.get('文件名', '') and '8.1' in m.get('文件名', '')) or ('课时2' in m.get('文件名', '') and '8.1' in m.get('文件名', ''))]

print(f'找到{len(coursewares)}个课时课件:')
for c in coursewares[:5]:
    print(f"  - 文件名: {c.get('文件名')}")
    print(f"    resource_type: {c.get('resource_type')}")
    print(f"    教学用途: {c.get('教学用途')}")
    print()
