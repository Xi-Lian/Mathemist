"""
从向量数据库中删除错误的"章末复习"课件记录
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()
coll = client.get_collection('math_resources_geometry')

print("=" * 80)
print("查找并删除错误的'章末复习'课件记录")
print("=" * 80)

# 查找所有包含"章末复习"的课件
results = coll.get(
    where={'resource_type': 'courseware'},
    include=['metadatas', 'documents']
)

print(f"\n总课件数量: {len(results['metadatas'])}")

# 查找包含"章末复习"的课件
to_delete_ids = []
for i, metadata in enumerate(results['metadatas']):
    filename = metadata.get('文件名', '')
    title = metadata.get('title', '')
    
    if '章末复习' in filename or '章末复习' in title:
        doc_id = results['ids'][i]
        print(f"\n找到错误记录:")
        print(f"  ID: {doc_id}")
        print(f"  文件名: {filename}")
        print(f"  标题: {title[:80]}")
        print(f"  教学用途: {metadata.get('教学用途', '')}")
        cloud_url = metadata.get('云端链接', '')
        print(f"  云端链接: {cloud_url[:100] if cloud_url else '无'}")
        
        to_delete_ids.append(doc_id)

if to_delete_ids:
    print(f"\n" + "=" * 80)
    print(f"准备删除 {len(to_delete_ids)} 条错误记录")
    print("=" * 80)
    
    confirm = input("\n确认删除这些记录吗？(yes/no): ")
    if confirm.lower() == 'yes':
        try:
            coll.delete(ids=to_delete_ids)
            print(f"\n[成功] 成功删除 {len(to_delete_ids)} 条记录")
            
            # 验证删除
            remaining = coll.get(
                where={'resource_type': 'courseware'},
                include=['metadatas']
            )
            
            remaining_complex = [m for m in remaining['metadatas'] 
                               if '章末复习' in m.get('文件名', '') or '章末复习' in m.get('title', '')]
            
            if len(remaining_complex) == 0:
                print("[成功] 验证通过：所有'章末复习'记录已删除")
            else:
                print(f"[警告] 仍有 {len(remaining_complex)} 条'章末复习'记录未删除")
                
        except Exception as e:
            print(f"\n[失败] 删除失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("\n[取消] 取消删除操作")
else:
    print("\n[完成] 未找到需要删除的记录")
