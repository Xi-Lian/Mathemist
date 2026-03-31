from .._shared import *


def analyze_query_modes(retriever, all_results):
    is_comparison_query = False
    themes = [theme for theme, _ in all_results]
    if len(all_results) >= 2:
        if hasattr(retriever, "_current_query_features") and retriever._current_query_features:
            query = retriever._current_query_features.get("original_query", "")
            if any(keyword in query for keyword in ["对比", "比较", "区别", "联系"]):
                is_comparison_query = True
                print(f"   🔍 V47.0检测到对比查询: {themes}")
        elif any(any(keyword in theme for keyword in ["对比", "比较", "区别", "联系"]) for theme in themes):
            is_comparison_query = True
            print(f"   🔍 V47.0检测到对比查询: {themes}")
        elif len(themes) == 2:
            function_themes = ["指数函数", "对数函数", "三角函数", "二次函数", "幂函数", "一次函数"]
            if all(theme in function_themes for theme in themes):
                is_comparison_query = True
                print(f"   🔍 V48.0检测到函数对比查询: {themes}")

    function_property_themes = ["函数的单调性", "函数的奇偶性", "函数的周期性"]
    is_function_property_query = any(theme in function_property_themes for theme in themes)
    if is_function_property_query:
        print(f"   🔍 检测到函数性质主题查询: {themes}")
    return themes, is_comparison_query, is_function_property_query


def collect_seen_resources(all_results, all_themes, is_comparison_query, is_function_property_query):
    theme_matcher_v90 = get_theme_matcher_v90()
    seen_resources = {}
    for theme, theme_results in all_results:
        if not theme_results.get("documents") or not theme_results["documents"][0]:
            continue

        docs = theme_results["documents"][0]
        metas = theme_results["metadatas"][0]
        dists = theme_results["distances"][0]
        ids = theme_results.get("ids", [[]])[0] if theme_results.get("ids") else [f"{theme}_{i}" for i in range(len(docs))]
        print(f"   📊 主题 '{theme}' 检索到 {len(docs)} 个结果")
        _print_distance_stats(metas, dists)

        for doc, meta, dist, id_ in zip(docs, metas, dists, ids):
            if dist >= _get_collect_threshold(meta.get("resource_type", ""), theme, len(all_themes), is_comparison_query, is_function_property_query):
                continue
            if not _passes_exclusion(theme_matcher_v90, meta, doc, theme, all_themes):
                continue
            _record_resource_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query)

    return seen_resources


def _get_collect_threshold(resource_type, theme, num_themes, is_comparison_query, is_function_property_query):
    if resource_type == "courseware":
        base_threshold = 2.5
        print(f"   🔍 V62.0课件资源：使用宽松阈值 {base_threshold}")
    elif resource_type == "lesson_plan":
        base_threshold = 2.5
        print(f"   🔍 V63.0教案资源：使用宽松阈值 {base_threshold}")
    elif is_comparison_query:
        base_threshold = 1.5
        print(f"   🔍 V47.0对比查询：使用宽松阈值 {base_threshold}")
    elif any(keyword in theme for keyword in ["应用", "实际", "生活"]):
        base_threshold = 1.8
        print(f"   🔍 V51.0应用题查询：使用宽松阈值 {base_threshold}")
    elif is_function_property_query:
        base_threshold = 1.0 if num_themes > 1 else 1.5
        print(f"   🔍 {'V100.0多主题函数性质查询' if num_themes > 1 else '函数性质查询'}：使用{'严格' if num_themes > 1 else ''}阈值 {base_threshold}")
    else:
        base_threshold = 0.9 if num_themes > 1 else 1.0
        if num_themes > 1:
            print(f"   🔍 V100.0多主题查询：使用严格阈值 {base_threshold}")
    return base_threshold


def _passes_exclusion(theme_matcher_v90, meta, doc, theme, all_themes):
    exclusion_factor = theme_matcher_v90._calculate_exclusion_factor(theme, meta.get("title", ""), doc, all_themes)
    if exclusion_factor == 0.0:
        print(f"      ⚠️ 排除：'{meta.get('title', '未知')}' 包含排除词 (主题: {theme})")
        return False
    if meta.get("resource_type", "") == "exercise":
        print(f"      ✅ 习题资源通过排除词检查: '{meta.get('title', '未知')}' (主题: {theme})")
    return True


def _record_resource_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query):
    unique_key = f"{meta.get('source_file', '')}_{meta.get('title', '')}"
    if unique_key not in seen_resources:
        seen_resources[unique_key] = {
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": id_,
            "matched_themes": [theme],
            "theme_distances": {theme: dist},
        }
        print(f"      ✅ 新资源 '{meta.get('title', '未知')}' 匹配主题 '{theme}' (距离: {dist:.3f})")
        return

    if theme not in seen_resources[unique_key]["matched_themes"]:
        similarity_threshold = 1.0 if is_function_property_query else 0.7
        if dist < similarity_threshold:
            seen_resources[unique_key]["matched_themes"].append(theme)
            seen_resources[unique_key]["theme_distances"][theme] = dist
            print(f"      ➕ 资源 '{meta.get('title', '未知')}' 新增匹配主题 '{theme}' (距离: {dist:.3f})")
        else:
            print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与主题 '{theme}' 相似度不足 (距离: {dist:.3f} >= {similarity_threshold})，不添加匹配")
    else:
        print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 已匹配主题 '{theme}'")

    existing_meta = seen_resources[unique_key]["meta"]
    for key in ["resource_type", "title", "source_file"]:
        if (key not in existing_meta or not existing_meta[key]) and key in meta and meta[key]:
            existing_meta[key] = meta[key]


def _print_distance_stats(metas, dists):
    if not dists:
        return
    min_dist = min(dists)
    max_dist = max(dists)
    avg_dist = sum(dists) / len(dists)
    print(f"      📏 距离统计: 最小={min_dist:.4f}, 最大={max_dist:.4f}, 平均={avg_dist:.4f}")
    for i in range(min(5, len(dists))):
        title = metas[i].get("title", "未知")[:30]
        print(f"         - {title}... 距离={dists[i]:.4f}")
