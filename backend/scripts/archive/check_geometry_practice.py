#!/usr/bin/env python
import os
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def check_geometry_practice():
    print("检查几何板块中的练习课课件")
    print("="*60)

    import chromadb

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")

    # 获取几何板块集合
    geometry_coll = client.get_collection("math_resources_geometry")
    results = geometry_coll.get()

    metadatas = results.get('metadatas', [])

    # 统计几何板块中的课件
    courseware_count = 0
    practice_count = 0
    practice_titles = []

    for meta in metadatas:
        if meta.get("resource_type") == 'courseware':
            courseware_count += 1
            teaching_use = meta.get("教学用途", "未知")
            if "练习课" in teaching_use:
                practice_count += 1
                title = meta.get("title", "")
                practice_titles.append(title)

    print("几何板块课件统计:")
    print("  课件总数: " + str(courseware_count))
    print("  练习课课件数: " + str(practice_count))
    print("")
    print("练习课课件列表 (前20个):")
    for i, title in enumerate(practice_titles[:20], 1):
        print("  [" + str(i) + "] " + title)

    if len(practice_titles) > 20:
        print("  ... 还有 " + str(len(practice_titles) - 20) + " 个练习课课件")

    # 检查检索时是否限定了板块
    print("")
    print("检查检索范围:")
    print("  当前向量数据库有以下板块:")
    collections = client.list_collections()
    for coll in collections:
        print("    - " + coll.name)

    return True

if __name__ == "__main__":
    try:
        check_geometry_practice()
    except Exception as e:
        print("出错: " + str(e))
        import traceback
        traceback.print_exc()
