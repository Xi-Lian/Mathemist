#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_practice_courseware():
    """检查练习课课件在向量数据库中的分布"""
    print("检查练习课课件在向量数据库中的分布")
    print("="*60)
    
    import chromadb
    
    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    
    # 获取几何板块集合
    geometry_coll = client.get_collection("math_resources_geometry")
    results = geometry_coll.get()
    
    metadatas = results.get('metadatas', [])
    
    # 统计教学用途分布
    teaching_use_counts = {}
    courseware_by_use = {}
    
    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            teaching_use = meta.get("教学用途", "未知")
            teaching_use_counts[teaching_use] = teaching_use_counts.get(teaching_use, 0) + 1
            
            if teaching_use not in courseware_by_use:
                courseware_by_use[teaching_use] = []
            courseware_by_use[teaching_use].append({
                'title': meta.get('title', ''),
                'source_file': meta.get('source_file', '')
            })
    
    print(f"几何板块课件总数: {sum(teaching_use_counts.values())}")
    print("\n教学用途分布:")
    for use, count in teaching_use_counts.items():
        print(f"  {use}: {count}")
    
    # 显示练习课课件示例
    print("\n练习课课件示例 (前10个):")
    practice_list = courseware_by_use.get('练习课课件', [])
    for i, c in enumerate(practice_list[:10]):
        print(f"  [{i+1}] {c['title']}")
    
    # 检查这些练习课课件是否与检索返回的重复
    print("\n检索返回的课件标题 (前10个):")
    retrieved_titles = [
        "8.3.1 棱柱、棱锥、棱台的表面积和体积",
        "8.1课时2 圆柱、圆锥、圆台和球",
        "8.3 第1课时",
        "8.3 简单几何体的表面积与体积",
        "8.3.2 圆柱、圆锥、圆台、球的表面积和体积",
    ]
    for i, title in enumerate(retrieved_titles):
        # 检查是否在练习课课件中
        is_practice = any(title in c['title'] for c in practice_list)
        print(f"  [{i+1}] {title} {'(练习课课件)' if is_practice else '(非练习课课件)'}")
    
    return True

if __name__ == "__main__":
    try:
        check_practice_courseware()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
