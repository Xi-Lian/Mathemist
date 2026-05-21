#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_classify_issue():
    print("测试分类问题")
    print("="*60)

    import chromadb
    from app.core.model_config import model_config

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    embedding_model = model_config.get_embedding_model()

    query = "组合数 练习课 课件"
    query_emb = embedding_model.encode([query])

    prob_coll = client.get_collection("math_resources_probability")
    results = prob_coll.query(
        query_embeddings=query_emb.tolist(),
        n_results=30,
        where={"resource_type": "courseware"},
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n向量检索找到 {len(results['documents'][0])} 条结果")

    # 测试每条资源的分类情况
    from app.core.retrieval.classify_results_helpers.resource_type import normalize_resource_type, matches_requested_resource_type
    from app.core.retrieval.methods.classify_results import _ClassifyResultsMixin
    from app.config.resource_type_config import get_db_type, get_resource_type_mapping

    resource_types = ["课件", "习题"]

    print(f"\n测试每条资源的分类情况:")
    print(f"resource_types: {resource_types}")

    passed = 0
    failed = 0

    for i, (doc, meta, dist) in enumerate(zip(
        results['documents'][0][:10],
        results['metadatas'][0][:10],
        results['distances'][0][:10]
    ), 1):

        original_type = meta.get("resource_type", "unknown")
        normalized_type = normalize_resource_type(meta, original_type)

        # 检查get_db_type
        db_type_课件 = get_db_type("课件")
        db_type_习题 = get_db_type("习题")

        # 检查get_resource_type_mapping
        mapping_课件 = get_resource_type_mapping("课件")
        mapping_习题 = get_resource_type_mapping("习题")

        matched = matches_requested_resource_type(normalized_type, resource_types)

        print(f"\n[{i}] title: {meta.get('title', '')[:40]}")
        print(f"    original_type: {original_type}")
        print(f"    normalized_type: {normalized_type}")
        print(f"    matches: {matched}")
        print(f"    distance: {dist:.4f}")

        if matched:
            passed += 1
        else:
            failed += 1

    print(f"\n总结: 通过={passed}, 失败={failed}")

if __name__ == "__main__":
    test_classify_issue()