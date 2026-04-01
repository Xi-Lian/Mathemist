from .._shared import *
from .filters import (
    adjust_single_theme_result_count,
    build_resource_type_filters,
    has_specific_resource_types,
)

SEMANTIC_RESOURCE_TYPES = {
    "教案",
    "教学设计",
    "教学方案",
    "教学计划",
    "备课",
    "导学案",
    "详案",
    "简案",
    "教学反思",
    "核心素养",
    "课件",
    "PPT",
    "幻灯片",
    "演示文稿",
    "课件资源",
    "教学大纲",
    "大纲",
    "课程标准",
}


def _should_preserve_query_text(resource_types):
    return bool(resource_types) and any(rt in SEMANTIC_RESOURCE_TYPES for rt in resource_types)


def _is_general_material_query(query, resource_types):
    generic_words = ["资料", "学习资料", "教学资源", "资源", "内容"]
    return (not resource_types or any(rt in {"资料", "资源", "教学资源", "学习资料"} for rt in resource_types)) and any(
        word in (query or "") for word in generic_words
    )


def _should_apply_semantic_supplement(query, resource_types, core_theme):
    return bool(core_theme) and (_should_preserve_query_text(resource_types) or _is_general_material_query(query, resource_types))


def _text_match_score(core_theme, metadata, document):
    title = metadata.get("title", "") or ""
    source_file = metadata.get("source_file", "") or ""
    knowledge_tags = metadata.get("知识点标签", "") or metadata.get("知识点", "") or ""
    text = f"{title} {source_file} {knowledge_tags} {document or ''}"

    if core_theme in title:
        return 1.0
    if core_theme in source_file:
        return 0.9
    if core_theme in knowledge_tags:
        return 0.85
    if core_theme in text:
        return 0.7
    return 0.0


def _build_semantic_supplement(collection, where_filter, core_theme, limit):
    try:
        if where_filter:
            raw = collection.get(where=where_filter, include=["documents", "metadatas"])
        else:
            raw = collection.get(include=["documents", "metadatas"])
    except Exception as exc:
        print(f"   ⚠️ 语义补召回失败: {exc}")
        return None

    documents = raw.get("documents") or []
    metadatas = raw.get("metadatas") or []
    ids = raw.get("ids") or []
    scored = []

    for index, metadata in enumerate(metadatas):
        document = documents[index] if index < len(documents) else ""
        score = _text_match_score(core_theme, metadata or {}, document or "")
        if score <= 0:
            continue
        scored.append((score, document, metadata or {}, ids[index] if index < len(ids) else f"supplement_{index}"))

    if not scored:
        return None

    scored.sort(key=lambda item: -item[0])
    top_items = scored[:limit]
    print(f"   🔎 语义补召回命中 {len(top_items)} 条，主题='{core_theme}'")

    return {
        "documents": [[item[1] for item in top_items]],
        "metadatas": [[item[2] for item in top_items]],
        "distances": [[max(0.05, 0.6 - item[0] * 0.4) for item in top_items]],
        "ids": [[f"semantic_{item[3]}" for item in top_items]],
    }


def _merge_query_results(primary_results, supplement_results):
    if not primary_results:
        return supplement_results
    if not supplement_results:
        return primary_results

    merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for key in ("documents", "metadatas", "distances", "ids"):
        merged[key][0].extend(primary_results.get(key, [[]])[0] if primary_results.get(key) else [])
        merged[key][0].extend(supplement_results.get(key, [[]])[0] if supplement_results.get(key) else [])
    return merged


def execute_single_theme_retrieval(
    retriever,
    collection,
    query,
    core_theme,
    n_results,
    resource_types,
    question_type,
):
    if has_specific_resource_types(resource_types):
        query_to_use = query
        print(f"\n🔍 V83.0执行资源类型查询，使用原始查询作为查询文本: '{query_to_use}'")
    else:
        if not core_theme:
            core_theme = "函数"
            print(f"   📝 V66.0使用默认主题: '{core_theme}'")
        query_to_use = core_theme
        print(f"\n🔍 执行单主题检索，查询: '{query_to_use}'")

    resource_type_filters, where_filter = build_resource_type_filters(query, resource_types, question_type)
    detected_intents = retriever._detect_query_intents(query)

    if core_theme:
        if _should_preserve_query_text(resource_types):
            enhanced_query = query_to_use
            print(f"   🔍 V51.1保留资源类型语义作为查询文本: '{enhanced_query}'")
        else:
            enhanced_query = core_theme
            print(f"   🔍 V51.0使用核心主题作为查询文本: '{enhanced_query}'")
    else:
        enhanced_query = retriever._enhance_query_dynamically(query_to_use, detected_intents)
        print(f"   🔍 V51.0动态查询增强: '{query_to_use}' -> '{enhanced_query}'")

    n_results_per_query = n_results or retriever.DEFAULT_N_RESULTS
    n_results_adjusted = adjust_single_theme_result_count(
        retriever,
        query,
        query_to_use,
        detected_intents,
        n_results_per_query,
        core_theme,
        question_type,
        resource_types,
    )

    if resource_type_filters:
        print(f"\n  🔍 V54.1组合资源查询: 为 {len(resource_type_filters)} 种资源类型单独检索")
        all_results = []
        for resource_filter in resource_type_filters:
            resource_type = resource_filter["resource_type"]
            print(f"\n  🔍 为资源类型 '{resource_type}' 执行检索...")
            print("   📋 V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索")
            theme_results = collection.query(
                query_texts=[enhanced_query],
                n_results=n_results_adjusted,
                where=resource_filter,
                include=["documents", "metadatas", "distances"],
            )
            theme_results["ids"] = [[f"{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
            if theme_results.get("documents") and theme_results["documents"][0]:
                print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
                all_results.append((resource_type, theme_results))
            else:
                print("     ❌ 未找到结果")

        if all_results:
            print(f"\n🔄 合并 {len(all_results)} 种资源类型的检索结果...")
            results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
            for resource_type, theme_results in all_results:
                results["documents"][0].extend(theme_results["documents"][0])
                results["metadatas"][0].extend(theme_results["metadatas"][0])
                results["distances"][0].extend(theme_results["distances"][0])
                results["ids"][0].extend(theme_results["ids"][0])
            print(f"✅ 合并完成，共 {len(results['documents'][0])} 条结果")
        else:
            print("❌ 所有资源类型均未找到结果")
            results = None
    else:
        print("   📋 V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索")
        results = collection.query(
            query_texts=[enhanced_query],
            n_results=n_results_adjusted,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]

    supplement_where = where_filter
    if _is_general_material_query(query, resource_types):
        supplement_where = None

    if _should_apply_semantic_supplement(query, resource_types, core_theme):
        supplement_results = _build_semantic_supplement(
            collection,
            supplement_where,
            core_theme,
            limit=min(40, max(10, n_results_adjusted // 4)),
        )
        results = _merge_query_results(results, supplement_results)

    return query_to_use, core_theme, results


def postprocess_single_theme_results(retriever, query, results, resource_types, core_theme):
    if not (results and results.get("documents") and results["documents"][0]):
        return None

    if not results.get("ids") or not results["ids"][0]:
        results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]

    if results.get("metadatas") and results["metadatas"][0]:
        unique_results = retriever._deduplicate_results(results)
        print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
        results = unique_results

    filtered_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    for doc, meta, dist, id_ in zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]):
        if _passes_unified_semantic_gate(query, core_theme, doc, meta, dist):
            filtered_results["documents"][0].append(doc)
            filtered_results["metadatas"][0].append(meta)
            filtered_results["distances"][0].append(dist)
            filtered_results["ids"][0].append(id_)
            print(f"   ✅ 保留：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
        else:
            print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 语义门控未通过 (距离: {dist:.3f})")

    if filtered_results["documents"][0]:
        print(f"   ✅ V64.0单主题查询过滤完成，保留 {len(filtered_results['documents'][0])} 条结果")
        return filtered_results

    print("   ❌ V64.0单主题查询过滤后无结果")
    return None


def _passes_unified_semantic_gate(query, core_theme, doc, meta, distance):
    if distance is None:
        return False
    if distance <= 0.95:
        return True
    if not core_theme:
        return distance <= 1.10

    text = f"{doc} {meta.get('title', '')} {meta.get('知识点', '')} {meta.get('知识点标签', '')} {meta.get('source_file', '')}"
    if core_theme in text:
        return True
    return distance <= 1.05
