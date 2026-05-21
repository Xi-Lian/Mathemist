#!/usr/bin/env python
import sys
sys.path.insert(0, "D:/Git_Repository/Mathemist/backend")

def test_classification():
    print("测试分类逻辑")
    print("="*60)

    # 导入必要的函数
    from app.core.retrieval.classify_results_helpers.resource_type import normalize_resource_type, matches_requested_resource_type
    from app.config.resource_type_config import get_db_type, get_resource_type_mapping

    # 模拟一个"组合数 练习课 课件"的资源metadata
    test_metadata = {
        "resource_type": "courseware",
        "title": "组合数的综合应用(习题课) - 组合数的综合应用(习题课)",
        "source_file": "概率与统计-课件汇总.xlsx",
        "教学用途": "练习课课件",
        "board": "概率统计"
    }

    resource_types = ["课件", "习题"]

    print("\n[步骤1] 测试normalize_resource_type")
    normalized_type = normalize_resource_type(test_metadata, test_metadata.get("resource_type", "theory"))
    print(f"  原始resource_type: {test_metadata.get('resource_type')}")
    print(f"  归一化后: {normalized_type}")

    print("\n[步骤2] 测试get_db_type")
    for rt in resource_types:
        mapped = get_db_type(rt)
        print(f"  get_db_type('{rt}'): {mapped}")

    print("\n[步骤3] 测试get_resource_type_mapping")
    for rt in resource_types:
        mapped = get_resource_type_mapping(rt)
        print(f"  get_resource_type_mapping('{rt}'): {mapped}")

    print("\n[步骤4] 测试matches_requested_resource_type")
    matched = matches_requested_resource_type(normalized_type, resource_types)
    print(f"  matches_requested_resource_type('{normalized_type}', {resource_types}): {matched}")

    # 测试实际的向量检索+分类流程
    print("\n" + "="*60)
    print("[步骤5] 测试完整的向量检索+分类流程")

    import chromadb
    from app.core.model_config import model_config

    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    embedding_model = model_config.get_embedding_model()

    query = "组合数 练习课 课件"
    query_emb = embedding_model.encode([query])

    prob_coll = client.get_collection("math_resources_probability")
    results = prob_coll.query(
        query_embeddings=query_emb.tolist(),
        n_results=10,
        where={"resource_type": "courseware"},
        include=["documents", "metadatas", "distances"]
    )

    print(f"\n  向量检索结果: {len(results['documents'][0])} 条")

    # 测试分类
    from app.core.retrieval.methods.classify_results import _ClassifyResultsMixin

    classifier = _ClassifyResultsMixin()

    # 模拟postprocess_single_theme_results的结果格式
    mock_results = {
        "documents": results["documents"],
        "metadatas": results["metadatas"],
        "distances": results["distances"]
    }

    classified = classifier._classify_results(
        results=mock_results,
        resource_types=resource_types,
        core_theme="组合数",
        query=query
    )

    print(f"\n  分类后结果:")
    for category, resources in classified.items():
        if resources:
            print(f"    {category}: {len(resources)} 条")

if __name__ == "__main__":
    test_classification()