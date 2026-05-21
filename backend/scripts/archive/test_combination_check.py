#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_combination_resource():
    print("检查向量数据库中'组合数'相关资源的metadata")
    print("="*60)

    import chromadb

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")

    # 获取概率统计板块
    prob_coll = client.get_collection("math_resources_probability")

    # 检索包含"组合"或"组合数"的资源
    results = prob_coll.get(
        where={"resource_type": "courseware"},
        include=["metadatas"]
    )

    print(f"概率统计板块课件总数: {len(results.get('metadatas', []))}")

    # 查找包含"组合"关键词的资源
    combination_resources = []
    for meta in results.get('metadatas', []):
        title = meta.get('title', '') or ''
        content = meta.get('content', '') or ''

        if '组合' in title or '组合' in content:
            combination_resources.append(meta)

    print(f"包含'组合'关键词的资源数: {len(combination_resources)}")

    if combination_resources:
        print("\n示例资源metadata:")
        for i, meta in enumerate(combination_resources[:3], 1):
            print(f"\n[{i}] 标题: {meta.get('title', '')[:50]}")
            print(f"    知识点: {meta.get('knowledge_points', 'N/A')}")
            print(f"    教学用途: {meta.get('教学用途', 'N/A')}")

    # 测试向量检索
    print("\n" + "="*60)
    print("测试向量检索'组合数'")

    from app.core.model_config import model_config
    embedding_model = model_config.get_embedding_model()

    query_emb = embedding_model.encode(["组合数 练习课 课件"])
    results = prob_coll.query(
        query_embeddings=query_emb.tolist(),
        n_results=10,
        where={"resource_type": "courseware"},
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n检索到 {len(results['documents'][0])} 条结果")

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0][:5],
        results['metadatas'][0][:5],
        results['distances'][0][:5]
    ), 1):
        print(f"\n[{i}] 距离: {dist:.4f}")
        print(f"    标题: {meta.get('title', '')[:50]}")
        print(f"    知识点: {meta.get('knowledge_points', 'N/A')}")
        print(f"    教学用途: {meta.get('教学用途', 'N/A')}")

if __name__ == "__main__":
    test_combination_resource()