#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_algebra_courseware():
    """检查代数板块课件的来源"""
    print("检查代数板块课件的来源")
    print("="*60)
    
    import chromadb
    
    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    
    # 获取代数板块集合
    algebra_coll = client.get_collection("math_resources_algebra")
    results = algebra_coll.get()
    
    metadatas = results.get('metadatas', [])
    
    # 统计课件来源
    source_counts = {}
    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            source_file = meta.get("source_file", "未知")
            source_counts[source_file] = source_counts.get(source_file, 0) + 1
    
    print("代数板块课件来源统计:")
    for source, count in source_counts.items():
        print(f"  {source}: {count} 条")
    
    # 检查是否有共享逻辑
    print("\n检查共享逻辑...")
    shared_count = 0
    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            source_file = meta.get("source_file", "")
            if "立体几何" in source_file:
                shared_count += 1
    
    print(f"从几何板块共享到代数板块的课件数量: {shared_count}")
    
    return True

if __name__ == "__main__":
    try:
        check_algebra_courseware()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
