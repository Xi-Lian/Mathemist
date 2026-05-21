#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_parallel_query():
    print("测试并行查询执行")
    print("="*60)

    import chromadb
    from app.core.model_config import model_config

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    embedding_model = model_config.get_embedding_model()

    # 测试1: 直接向量检索
    print("\n[测试1] 直接向量检索")
    query = "组合数 练习课 课件"
    query_emb = embedding_model.encode([query])

    prob_coll = client.get_collection("math_resources_probability")
    results = prob_coll.query(
        query_embeddings=query_emb.tolist(),
        n_results=10,
        where={"resource_type": "courseware"},
        include=["documents", "metadatas", "distances"]
    )

    print(f"  查询: '{query}'")
    print(f"  检索到 {len(results['documents'][0])} 条结果")

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0][:5],
        results['metadatas'][0][:5],
        results['distances'][0][:5]
    ), 1):
        print(f"  [{i}] distance={dist:.4f}, title={meta.get('title', '')[:40]}")

    # 测试2: 模拟查询变体
    print("\n[测试2] 测试查询变体")
    query_variants = ['组合数 练习课 课件', '组合数 习题课 课件', '组合与组合数 练习课 PPT']

    for variant in query_variants:
        variant_emb = embedding_model.encode([variant])
        results = prob_coll.query(
            query_embeddings=variant_emb.tolist(),
            n_results=5,
            where={"resource_type": "courseware"},
            include=["documents", "metadatas", "distances"]
        )
        print(f"  查询: '{variant}' -> {len(results['documents'][0])} 条结果")

        if results['documents'][0]:
            for i, (doc, meta, dist) in enumerate(zip(
                results['documents'][0][:3],
                results['metadatas'][0][:3],
                results['distances'][0][:3]
            ), 1):
                teaching_use = meta.get('教学用途', '')
                marker = "*练习课*" if '练习课' in teaching_use else ""
                print(f"    [{i}] distance={dist:.4f}, {teaching_use} {marker}, title={meta.get('title', '')[:40]}")

    # 测试3: 检查文档embedding
    print("\n[测试3] 检查文档embedding内容")
    # 获取一个包含"组合数"的资源
    all_results = prob_coll.get(
        where={"resource_type": "courseware"},
        include=["documents", "metadatas"]
    )

    for meta, doc in zip(all_results['metadatas'], all_results['documents']):
        title = meta.get('title', '') or ''
        if '组合数' in title:
            print(f"  文档: {doc[:100]}...")
            print(f"  元数据: title={title}, 教学用途={meta.get('教学用途', '')}")
            break

if __name__ == "__main__":
    test_parallel_query()