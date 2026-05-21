"""
快速诊断棱柱课件问题 - 直接查询ChromaDB
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

def quick_diagnose():
    """快速诊断"""
    
    print("=" * 80)
    print("快速诊断棱柱课件")
    print("=" * 80)
    
    # 创建VectorDatabaseBuilder实例
    learning_resource_path = os.path.join(os.path.dirname(__file__), 'learning_resource')
    vdb_builder = VectorDatabaseBuilder(learning_resource_path)
    client = vdb_builder.get_chroma_client()
    
    # 查询几何板块的集合
    collection_name = "math_resources_geometry"
    
    print(f"\n检查集合: {collection_name}")
    
    # 获取集合
    try:
        collection = client.get_collection(name=collection_name)
        
        # 获取所有资源
        results = collection.get(
            include=["metadatas", "documents"]
        )
        
        print(f"\n找到 {len(results['ids'])} 个总资源")
        
        # 筛选课件
        courseware_results = []
        for doc_id, metadata, document in zip(
            results['ids'], 
            results['metadatas'], 
            results['documents']
        ):
            if metadata.get('resource_type') == 'courseware':
                courseware_results.append((doc_id, metadata, document))
        
        print(f"其中课件资源: {len(courseware_results)} 个")
        
        # 筛选包含"棱柱"的课件
        prism_courseware = []
        for doc_id, metadata, document in courseware_results:
            content = metadata.get('内容', '') or document or ''
            filename = metadata.get('文件名', '')
            teaching_use = metadata.get('教学用途', '')
            
            if '棱柱' in content or '棱柱' in filename:
                prism_courseware.append({
                    'id': doc_id,
                    'filename': filename,
                    'teaching_use': teaching_use,
                    'content_preview': content[:100] if content else '',
                    'knowledge_tags': metadata.get('知识点', ''),
                    'chapter': metadata.get('章节', ''),
                    'grade': metadata.get('年级', '')
                })
        
        print(f"\n找到 {len(prism_courseware)} 个包含'棱柱'的课件:")
        print("-" * 80)
        
        for i, cw in enumerate(prism_courseware, 1):
            print(f"\n{i}. 文件名: {cw['filename']}")
            print(f"   教学用途: {cw['teaching_use']}")
            print(f"   知识点: {cw['knowledge_tags']}")
            print(f"   章节: {cw['chapter']}")
            print(f"   年级: {cw['grade']}")
            print(f"   内容预览: {cw['content_preview']}...")
            
            # 特别标记那两个目标课件
            if '课时1' in cw['filename'] and '棱柱' in cw['filename']:
                print(f"   [TARGET] 这是目标课件1！")
            if '课时2' in cw['filename'] and ('棱柱' in cw['filename'] or '圆柱' in cw['filename']):
                print(f"   [TARGET] 这是目标课件2！")
        
        # 如果没有找到，列出所有课件的文件名
        if not prism_courseware:
            print("\n未找到包含'棱柱'的课件，列出前20个课件文件名:")
            all_courseware = list(zip(results['ids'], results['metadatas']))[:20]
            for doc_id, metadata in all_courseware:
                print(f"  - {metadata.get('文件名', 'N/A')}")
                
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    quick_diagnose()
