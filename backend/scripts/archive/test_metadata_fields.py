#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def check_actual_metadata_fields():
    print("检查向量数据库中实际的metadata字段")
    print("="*60)

    import chromadb

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")

    # 获取概率统计板块
    prob_coll = client.get_collection("math_resources_probability")

    # 获取一条资源的完整metadata
    results = prob_coll.get(
        where={"resource_type": "courseware"},
        include=["metadatas"],
        limit=1
    )

    if results.get('metadatas'):
        print("\n实际metadata字段:")
        for key, value in results['metadatas'][0].items():
            print(f"  - {key}: {str(value)[:80]}")

    # 检查是否有"组合"相关的资源
    print("\n" + "="*60)
    print("查找包含'组合'的练习课课件:")

    all_results = prob_coll.get(
        where={"resource_type": "courseware"},
        include=["metadatas"]
    )

    combination_practice = []
    for meta in all_results.get('metadatas', []):
        title = meta.get('title', '') or ''
        teaching_use = meta.get('教学用途', '') or ''

        if '组合' in title and '练习课' in teaching_use:
            combination_practice.append(meta)

    print(f"\n找到 {len(combination_practice)} 个包含'组合'的练习课课件:")
    for meta in combination_practice[:5]:
        print(f"  - {meta.get('title', '')[:50]}")

if __name__ == "__main__":
    check_actual_metadata_fields()