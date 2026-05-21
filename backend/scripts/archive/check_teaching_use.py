#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_teaching_use():
    """检查向量数据库中课件的'教学用途'字段"""
    print("检查向量数据库中课件的'教学用途'字段")
    print("="*60)
    
    import chromadb
    
    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    
    # 获取几何板块集合
    geometry_coll = client.get_collection("math_resources_geometry")
    results = geometry_coll.get()
    
    metadatas = results.get('metadatas', [])
    
    # 统计教学用途分布
    teaching_use_counts = {}
    courseware_count = 0
    
    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            courseware_count += 1
            teaching_use = meta.get("教学用途", "未知")
            teaching_use_counts[teaching_use] = teaching_use_counts.get(teaching_use, 0) + 1
    
    print(f"几何板块课件总数: {courseware_count}")
    print("\n教学用途分布:")
    for use, count in teaching_use_counts.items():
        print(f"  {use}: {count}")
    
    # 检查检索返回的课件是否有教学用途
    print("\n检索返回的课件示例:")
    sample_count = 0
    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            filename = meta.get("source_file", "")
            title = meta.get("title", "")
            teaching_use = meta.get("教学用途", "未知")
            
            if isinstance(filename, str):
                filename = filename.encode('gbk', errors='ignore').decode('gbk')
            
            print(f"  文件: {filename[:50]}")
            print(f"  标题: {title}")
            print(f"  教学用途: {teaching_use}")
            print()
            
            sample_count += 1
            if sample_count >= 5:
                break
    
    return True

if __name__ == "__main__":
    try:
        check_teaching_use()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
