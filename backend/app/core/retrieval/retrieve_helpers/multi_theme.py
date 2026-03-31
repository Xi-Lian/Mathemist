from .._shared import *
from .filters import adjust_multi_theme_result_count, build_resource_type_filters, simplify_themes


def execute_multi_theme_retrieval(
    retriever,
    collection,
    query,
    core_themes,
    n_results,
    resource_types,
    question_type,
):
    print(f"🔄 检测到多个主题({len(core_themes)}个)，采用分别检索策略: {core_themes}")
    themes_to_search = simplify_themes(core_themes)
    all_results = []
    detected_intents = retriever._detect_query_intents(query)
    resource_type_filters, where_filter = build_resource_type_filters(query, resource_types, question_type)

    if resource_type_filters:
        print(f"   🔍 开始执行组合资源查询，资源类型: {[rf['resource_type'] for rf in resource_type_filters]}")
        for resource_filter in resource_type_filters:
            if resource_filter["resource_type"] == "courseware":
                _query_courseware_for_multi_theme(
                    retriever, collection, query, n_results, detected_intents, resource_filter, all_results
                )

        for resource_filter in resource_type_filters:
            if resource_filter["resource_type"] != "courseware":
                for theme in themes_to_search:
                    _query_multi_theme_resource_type(
                        retriever,
                        collection,
                        query,
                        theme,
                        n_results,
                        detected_intents,
                        themes_to_search,
                        question_type,
                        resource_types,
                        resource_filter,
                        all_results,
                    )
    else:
        for theme in themes_to_search:
            _query_multi_theme(
                retriever,
                collection,
                query,
                theme,
                n_results,
                detected_intents,
                themes_to_search,
                question_type,
                resource_types,
                where_filter,
                all_results,
            )

    print("\n🔄 调用_merge_multi_theme_results函数...")
    merged_results = retriever._merge_multi_theme_results(all_results)
    print(f"✅ 合并完成，共 {len(merged_results['documents'][0])} 条结果")

    if merged_results and merged_results.get("metadatas") and merged_results["metadatas"][0]:
        unique_results = retriever._deduplicate_results(merged_results)
        print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
        results = unique_results
    else:
        results = merged_results

    if any(keyword in query for keyword in ["综合题", "综合", "综合练习", "数学综合"]):
        results = filter_comprehensive_results(merged_results, results)

    return results


def _query_courseware_for_multi_theme(retriever, collection, query, n_results, detected_intents, resource_filter, all_results):
    resource_type = resource_filter["resource_type"]
    print(f"\n  🔍 为资源类型 '{resource_type}' 执行检索...")
    n_results_per_theme = n_results or retriever.DEFAULT_N_RESULTS
    n_results_per_theme = retriever._adjust_retrieval_count(query, detected_intents, n_results_per_theme)
    print(f"   🔍 课件资源检索: 检索数量 {n_results_per_theme}")

    query_text = query
    print(f"   🔍 使用查询文本: '{query_text}' (资源类型: {resource_type})")
    print(f"     🔍 执行ChromaDB查询: resource_type={resource_filter['resource_type']}, n_results={n_results_per_theme}")
    theme_results = collection.query(
        query_texts=[query_text],
        n_results=n_results_per_theme,
        where=resource_filter,
        include=["documents", "metadatas", "distances"],
    )

    if theme_results.get("documents") and theme_results["documents"][0]:
        theme_results["ids"] = [[f"courseware_{i}" for i in range(len(theme_results["documents"][0]))]]
        print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条课件资源结果")
        for i in range(min(3, len(theme_results["documents"][0]))):
            meta = theme_results["metadatas"][0][i]
            print(f"       - 课件资源{i + 1}: {meta.get('title', '未知')}")
        all_results.append(("课件", theme_results))
    else:
        print("     ❌ 未找到课件资源结果")
        theme_results["ids"] = [["courseware_0"]]
        all_results.append(("课件", theme_results))


def _query_multi_theme_resource_type(
    retriever,
    collection,
    query,
    theme,
    n_results,
    detected_intents,
    themes_to_search,
    question_type,
    resource_types,
    resource_filter,
    all_results,
):
    resource_type = resource_filter["resource_type"]
    print(f"\n  🔍 为主题 '{theme}' 执行检索 (资源类型: {resource_type})...")
    base_count = n_results or retriever.DEFAULT_N_RESULTS
    n_results_per_theme = adjust_multi_theme_result_count(
        retriever,
        query,
        detected_intents,
        base_count,
        themes_to_search,
        theme,
        question_type,
        resource_types,
    )
    query_text = theme
    print(f"   🔍 使用查询文本: '{query_text}' (资源类型: {resource_type})")
    print(f"     🔍 执行ChromaDB查询: resource_type={resource_type}, n_results={n_results_per_theme}")
    theme_results = collection.query(
        query_texts=[query_text],
        n_results=n_results_per_theme,
        where=resource_filter,
        include=["documents", "metadatas", "distances"],
    )

    if theme_results.get("documents") and theme_results["documents"][0]:
        theme_results["ids"] = [[f"{theme}_{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
        print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
        all_results.append((theme, theme_results))
    else:
        print("     ❌ 未找到结果")
        theme_results["ids"] = [[f"{theme}_{resource_type}_0"]]
        all_results.append((theme, theme_results))


def _query_multi_theme(
    retriever,
    collection,
    query,
    theme,
    n_results,
    detected_intents,
    themes_to_search,
    question_type,
    resource_types,
    where_filter,
    all_results,
):
    print(f"\n  🔍 为主题 '{theme}' 执行检索...")
    base_count = n_results or retriever.DEFAULT_N_RESULTS
    n_results_per_theme = adjust_multi_theme_result_count(
        retriever,
        query,
        detected_intents,
        base_count,
        themes_to_search,
        theme,
        question_type,
        resource_types,
    )
    theme_results = collection.query(
        query_texts=[theme],
        n_results=n_results_per_theme,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )
    theme_results["ids"] = [[f"{theme}_{i}" for i in range(len(theme_results["documents"][0]))]]

    if theme_results.get("documents") and theme_results["documents"][0]:
        print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
        for i in range(min(3, len(theme_results["documents"][0]))):
            meta = theme_results["metadatas"][0][i]
            print(f"       - 结果{i + 1}: 题目类型={meta.get('题目类型', '未知')}, 来源={meta.get('source_file', '未知')}")
        all_results.append((theme, theme_results))
    else:
        print("     ❌ 未找到结果")


def filter_comprehensive_results(merged_results, current_results):
    print("\n✨ V10.0：检测到综合题查询，增强多主题匹配...")
    comprehensive_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    for i, meta in enumerate(merged_results["metadatas"][0]):
        doc = merged_results["documents"][0][i]
        question = meta.get("题干", "") or doc
        knowledge_tags = meta.get("知识点", "") or meta.get("知识点标签", "")
        is_comprehensive = False

        if len(question) > 150:
            is_comprehensive = True

        if not is_comprehensive and knowledge_tags:
            knowledge_points = [kp.strip() for kp in knowledge_tags.split(";") if kp.strip()]
            if len(knowledge_points) > 2:
                is_comprehensive = True

        if not is_comprehensive:
            comprehensive_keywords = ["综合", "应用", "实际问题", "多知识点", "跨章节", "综合题", "综合练习"]
            all_info = f"{question} {knowledge_tags} {meta.get('标题', '')}"
            is_comprehensive = any(keyword in all_info for keyword in comprehensive_keywords)

        if is_comprehensive:
            comprehensive_results["documents"][0].append(merged_results["documents"][0][i])
            comprehensive_results["metadatas"][0].append(merged_results["metadatas"][0][i])
            comprehensive_results["distances"][0].append(merged_results["distances"][0][i])
            comprehensive_results["ids"][0].append(merged_results["ids"][0][i])

    if comprehensive_results["documents"][0]:
        print(f"✅ 筛选出 {len(comprehensive_results['documents'][0])} 条综合题")
        return comprehensive_results

    print("⚠️ 未找到综合题，返回原始结果")
    return current_results
