from .._shared import *
from .filters import adjust_multi_theme_result_count, build_resource_type_filters, simplify_themes
from .semantic_matcher import semantic_matcher


def execute_multi_theme_retrieval(
    retriever,
    collection,
    query,
    core_themes,
    n_results,
    resource_types,
    question_type,
    requirements=None,
):
    # core_themes 是一个元组 (主题字符串或主题列表, 板块名称)
    # 如果主题是逗号分隔的字符串，需要先拆分
    raw_themes = core_themes[0] if isinstance(core_themes, tuple) else core_themes

    # 拆分逗号分隔的主题字符串
    if isinstance(raw_themes, str) and "," in raw_themes:
        theme_list = [t.strip() for t in raw_themes.split(",") if t.strip()]
    elif isinstance(raw_themes, list):
        theme_list = raw_themes
    else:
        theme_list = [raw_themes]

    print(f"🔄 检测到多个主题({len(theme_list)}个)，采用分别检索策略: {theme_list}")
    print(f"🔍 DEBUG: resource_types参数 = {resource_types}")
    themes_to_search = simplify_themes(theme_list)
    print(f"🔍 DEBUG: simplify_themes后 = {themes_to_search}")
    all_results = []
    detected_intents = retriever._detect_query_intents(query)
    resource_type_filters, where_filter = build_resource_type_filters(query, resource_types, question_type)
    print(f"🔍 DEBUG: resource_type_filters = {resource_type_filters}")
    print(f"🔍 DEBUG: where_filter = {where_filter}")

    if resource_type_filters:
        print(f"   🔍 开始执行组合资源查询，资源类型: {[rf['resource_type'] for rf in resource_type_filters]}")
        for resource_filter in resource_type_filters:
            if resource_filter["resource_type"] == "courseware":
                try:
                    _query_courseware_for_multi_theme(
                        retriever, collection, query, n_results, detected_intents, resource_filter, all_results
                    )
                except Exception as e:
                    print(f"   ⚠️ 课件资源查询失败: {str(e)}")
                    # 跳过课件资源查询，继续处理其他资源类型

        for resource_filter in resource_type_filters:
            if resource_filter["resource_type"] != "courseware":
                for theme in themes_to_search:
                    # 为每个主题获取正确的板块集合
                    theme_collection, early_result = retriever._ensure_collection_ready_for_theme(theme)
                    print(f"🔍 DEBUG: 主题 '{theme}' 获取集合结果: collection={theme_collection is not None}, early_result={early_result}")
                    if theme_collection:
                        _query_multi_theme_resource_type(
                            retriever,
                            theme_collection,
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
                        print(f"   ⚠️ 无法为主题 '{theme}' 获取集合，跳过")
    else:
        for theme in themes_to_search:
            # 为每个主题获取正确的板块集合
            theme_collection, early_result = retriever._ensure_collection_ready_for_theme(theme)
            print(f"🔍 DEBUG: 主题 '{theme}' 获取集合结果: collection={theme_collection is not None}, early_result={early_result}")
            if theme_collection:
                _query_multi_theme(
                    retriever,
                    theme_collection,
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
            else:
                print(f"   ⚠️ 无法为主题 '{theme}' 获取集合，跳过")

    print(f"🔍 DEBUG: all_results长度 = {len(all_results)}")
    if len(all_results) == 0:
        print("   ⚠️ 警告: all_results为空，没有任何检索结果")

    # 设置 _current_query_features 以便后续函数能够访问查询信息
    if not hasattr(retriever, '_current_query_features'):
        retriever._current_query_features = {}
    retriever._current_query_features['original_query'] = query

    # 检测是否分别查询
    is_separate_query = any(keyword in query for keyword in ["分别", "各自", "分开"])
    print(f"🔍 DEBUG: is_separate_query = {is_separate_query}")

    print("\n🔄 调用_merge_multi_theme_results函数...")
    merged_results = retriever._merge_multi_theme_results(all_results, is_separate_query)
    print(f"✅ 合并完成，共 {len(merged_results.get('documents', [[]])[0])} 条结果")

    if merged_results and merged_results.get("metadatas") and merged_results["metadatas"][0]:
        unique_results = retriever._deduplicate_results(merged_results)
        print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
        results = unique_results
    else:
        results = merged_results

    if requirements and results and results.get("documents") and results["documents"][0]:
        print(f"   🔍 使用语义匹配排序多主题检索结果，要求: {requirements}")
        results = _sort_multi_theme_results_by_semantic_score(results, requirements)
        print(f"   ✅ 多主题语义排序完成")

    if any(keyword in query for keyword in ["综合题", "综合", "综合练习", "数学综合"]):
        results = filter_comprehensive_results(merged_results, results)

    return results


def _sort_multi_theme_results_by_semantic_score(results, requirements):
    """
    根据语义匹配分数排序多主题检索结果
    
    Args:
        results: 检索结果
        requirements: 用户要求列表
    
    Returns:
        排序后的结果
    """
    if not requirements or not results.get("documents") or not results["documents"][0]:
        return results
    
    scored_items = []
    for i, (doc, meta, dist, id_) in enumerate(zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0], 
        results["ids"][0]
    )):
        semantic_score = 0.0
        for req in requirements:
            similarity = semantic_matcher.calculate_similarity_with_resource_type(req, doc, meta)
            semantic_score += similarity
        semantic_score = semantic_score / len(requirements) if requirements else 0.5
        
        scored_items.append({
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": id_,
            "semantic_score": semantic_score
        })
    
    scored_items.sort(key=lambda x: (-x["semantic_score"], x["dist"]))
    
    sorted_results = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
        "ids": [[]]
    }
    
    for item in scored_items:
        sorted_results["documents"][0].append(item["doc"])
        sorted_results["metadatas"][0].append(item["meta"])
        sorted_results["distances"][0].append(item["dist"])
        sorted_results["ids"][0].append(item["id"])
    
    return sorted_results


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
    # 使用更具体的查询文本，包含主题和资源类型
    resource_type_name = resource_filter.get("resource_type", "")
    # 映射资源类型代码到中文名称
    resource_type_map = {
        "lesson_plan": "教案",
        "courseware": "课件",
        "exercise": "习题",
        "syllabus": "教学大纲",
        "lesson_case": "课例",
        "ggb": "GGB"
    }
    resource_type_cn = resource_type_map.get(resource_type_name, resource_type_name)
    query_text = f"{theme} {resource_type_cn}"
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
    # 使用更具体的查询文本，包含主题和资源类型
    query_text = theme
    if resource_types:
        query_text = f"{theme} {' '.join(resource_types)}"
    print(f"   🔍 DEBUG _query_multi_theme: query_text='{query_text}', where_filter={where_filter}")
    print(f"   🔍 DEBUG _query_multi_theme: collection_name={collection.name}")
    theme_results = collection.query(
        query_texts=[query_text],
        n_results=n_results_per_theme,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )
    print(f"   🔍 DEBUG _query_multi_theme: 查询完成, 结果数量={len(theme_results.get('documents', [[]])[0]) if theme_results.get('documents') else 0}")

    if theme_results.get("documents") and theme_results["documents"][0]:
        theme_results["ids"] = [[f"{theme}_{i}" for i in range(len(theme_results["documents"][0]))]]
        print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
        for i in range(min(3, len(theme_results["documents"][0]))):
            meta = theme_results["metadatas"][0][i]
            print(f"       - 结果{i + 1}: 题目类型={meta.get('题目类型', '未知')}, 来源={meta.get('source_file', '未知')}")
        all_results.append((theme, theme_results))
    else:
        print("     ❌ 未找到结果")
        theme_results["ids"] = [[f"{theme}_0"]]
        all_results.append((theme, theme_results))


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
