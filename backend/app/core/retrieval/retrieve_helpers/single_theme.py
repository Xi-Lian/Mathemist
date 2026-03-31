from .._shared import *
from .filters import (
    adjust_single_theme_result_count,
    build_resource_type_filters,
    has_specific_resource_types,
)


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

    if has_specific_resource_types(resource_types):
        for doc, meta, dist, id_ in zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]):
            resource_type = meta.get("resource_type", "")
            strict_threshold = _get_specific_resource_threshold(retriever, query, resource_types, resource_type)
            contains_core_theme = core_theme and (
                core_theme in doc or core_theme in meta.get("title", "") or core_theme in str(meta)
            )
            if dist < strict_threshold or contains_core_theme:
                filtered_results["documents"][0].append(doc)
                filtered_results["metadatas"][0].append(meta)
                filtered_results["distances"][0].append(dist)
                filtered_results["ids"][0].append(id_)
                if contains_core_theme:
                    print(f"   ✅ 保留（包含核心主题）：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
                else:
                    print(f"   ✅ 保留：'{meta.get('title', '未知')}' (距离: {dist:.3f} < {strict_threshold})")
            else:
                print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 相似度过低 (距离: {dist:.3f} >= {strict_threshold})")
    else:
        for doc, meta, dist, id_ in zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]):
            resource_type = meta.get("resource_type", "")
            strict_threshold = _get_default_threshold(retriever, query, resource_type)
            print(f"   🔍 动态阈值调整：为{resource_type}资源使用阈值 {strict_threshold:.2f}")
            contains_core_theme = core_theme and (core_theme in doc or core_theme in meta.get("title", ""))
            if dist < strict_threshold or contains_core_theme:
                filtered_results["documents"][0].append(doc)
                filtered_results["metadatas"][0].append(meta)
                filtered_results["distances"][0].append(dist)
                filtered_results["ids"][0].append(id_)
                if contains_core_theme:
                    print(f"   ✅ 保留（包含核心主题）：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
                else:
                    print(f"   ✅ 保留：'{meta.get('title', '未知')}' (距离: {dist:.3f} < {strict_threshold:.2f})")
            else:
                print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 相似度过低 (距离: {dist:.3f} >= {strict_threshold:.2f})")

    if filtered_results["documents"][0]:
        print(f"   ✅ V64.0单主题查询过滤完成，保留 {len(filtered_results['documents'][0])} 条结果")
        return filtered_results

    print("   ❌ V64.0单主题查询过滤后无结果")
    return None


def _get_specific_resource_threshold(retriever, query, resource_types, resource_type=None):
    base_threshold = 1.5
    resource_type_adjustment = 0
    if any(rt in ["教案", "教学设计", "教学方案", "课件", "PPT", "幻灯片"] for rt in resource_types):
        resource_type_adjustment = 8.5
    elif any(rt in ["GGB", "GeoGebra", "动态图", "可视化"] for rt in resource_types):
        resource_type_adjustment = 6.0
    elif any(rt in ["习题", "题目", "练习题", "测试题"] for rt in resource_types):
        resource_type_adjustment = 1.5
    elif any(rt in ["课例", "教学视频", "课堂实录"] for rt in resource_types):
        resource_type_adjustment = 4.0
    elif any(rt in ["教学大纲", "大纲", "课程标准"] for rt in resource_types):
        resource_type_adjustment = 5.0

    intent_adjustment = 0
    intent = retriever._extract_query_conditions(query).get("intent", "")
    if intent == "练习":
        intent_adjustment = 0.5
    elif intent == "学习":
        intent_adjustment = 1.0
    elif intent == "教学":
        intent_adjustment = 2.0
    elif intent == "复习":
        intent_adjustment = 1.5
    elif intent == "比较":
        intent_adjustment = 2.5

    complexity_adjustment = 1.0 if len(query) > 30 else -0.5 if len(query) < 10 else 0

    if resource_type:
        if resource_type in {"courseware", "lesson_plan"}:
            resource_type_adjustment += 1.0
        elif resource_type == "exercise":
            resource_type_adjustment -= 0.5

    return max(1.0, min(15.0, base_threshold + resource_type_adjustment + intent_adjustment + complexity_adjustment))


def _get_default_threshold(retriever, query, resource_type):
    base_threshold = 1.5
    resource_type_adjustment = 0
    if resource_type in {"courseware", "lesson_plan"}:
        resource_type_adjustment = 1.5
    elif resource_type == "ggb":
        resource_type_adjustment = 2.0
    elif resource_type == "syllabus":
        resource_type_adjustment = 2.5
    elif resource_type == "lesson_case":
        resource_type_adjustment = 2.0

    intent_adjustment = 0
    intent = retriever._extract_query_conditions(query).get("intent", "")
    if intent == "练习":
        intent_adjustment = -0.5
    elif intent == "学习":
        intent_adjustment = 0.5
    elif intent == "教学":
        intent_adjustment = 1.0
    elif intent == "复习":
        intent_adjustment = 0.8
    elif intent == "比较":
        intent_adjustment = 1.2

    complexity_adjustment = 0.5 if len(query) > 30 else -0.3 if len(query) < 10 else 0
    return max(0.8, min(10.0, base_threshold + resource_type_adjustment + intent_adjustment + complexity_adjustment))
