from .._shared import *


def sort_and_filter_resources(retriever, seen_resources, all_themes, is_comparison_query):
    sorted_resources = sorted(
        seen_resources.values(),
        key=lambda x: (-len(x["matched_themes"]), sum(x["theme_distances"].values()) / len(x["theme_distances"]) - calculate_keyword_match_score(x, all_themes)),
    )

    filtered_resources = []
    print("\n🔍 开始过滤资源...")
    for resource in sorted_resources:
        min_distance = min(resource["theme_distances"].values())
        strict_threshold = _get_filter_threshold(retriever, resource, is_comparison_query)
        if min_distance > strict_threshold:
            print(f"      ⚠️ 过滤：'{resource['meta'].get('title', '未知')}' 相似度过低 (距离: {min_distance:.3f} > {strict_threshold})")
            continue
        if retriever._current_grade_info and not retriever._check_grade_match(resource["meta"], retriever._current_grade_info):
            print(f"      ⚠️ 年级筛选：'{resource['meta'].get('title', '未知')}' 不符合年级要求 {retriever._current_grade_info}")
            continue
        filtered_resources.append(resource)
        print(f"      ✅ 保留：'{resource['meta'].get('title', '未知')}' (匹配主题: {resource['matched_themes']})")
    print(f"✅ 过滤完成，保留 {len(filtered_resources)} 条相关结果")
    return filtered_resources


def build_merged_result(retriever, filtered_resources):
    merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for resource in filtered_resources:
        meta_with_themes = resource["meta"].copy()
        meta_with_themes["_matched_themes"] = resource["matched_themes"]
        meta_with_themes["_theme_distances"] = resource["theme_distances"]
        meta_with_themes["_matched_theme_count"] = len(resource["matched_themes"])
        merged["documents"][0].append(resource["doc"])
        merged["metadatas"][0].append(meta_with_themes)
        merged["distances"][0].append(resource["dist"])
        merged["ids"][0].append(resource["id"])

    print(f"✅ 合并完成，共 {len(merged['documents'][0])} 条唯一结果")
    if retriever._current_quantity_limit:
        print(f"🔍 应用数量限制：{retriever._current_quantity_limit} 条结果")
        for key in merged:
            if isinstance(merged[key], list) and merged[key]:
                merged[key][0] = merged[key][0][: retriever._current_quantity_limit]
        print(f"✅ 数量限制应用完成，保留 {len(merged['documents'][0])} 条结果")

    _print_match_summary(filtered_resources)
    return merged


def calculate_keyword_match_score(resource, all_themes):
    meta = resource["meta"]
    if meta.get("resource_type", "") != "lesson_plan":
        return 0.0

    title = meta.get("title", "")
    doc = resource["doc"]
    query_keywords = []
    for theme in all_themes:
        if "函数" in theme:
            query_keywords.append(theme)
            if "二次" in theme:
                query_keywords.append("二次函数")
            elif "三角" in theme:
                query_keywords.append("三角函数")
            elif "指数" in theme:
                query_keywords.append("指数函数")
            elif "对数" in theme:
                query_keywords.append("对数函数")
            elif "幂" in theme:
                query_keywords.append("幂函数")
            elif "一次" in theme:
                query_keywords.append("一次函数")

    keyword_match_score = 0.0
    for keyword in query_keywords:
        if keyword in title:
            keyword_match_score += 0.3
        if keyword in doc:
            keyword_match_score += 0.1
    return keyword_match_score


def _get_filter_threshold(retriever, resource, is_comparison_query):
    resource_type = resource["meta"].get("resource_type", "")
    if hasattr(retriever, "_loose_mode") and retriever._loose_mode:
        print("      🔍 V33.0宽松模式：使用阈值 2.0")
        return 2.0
    if resource_type == "courseware":
        print("      🔍 V62.0课件资源：使用宽松阈值 2.5")
        return 2.5
    if is_comparison_query:
        print("      🔍 V47.0对比查询：使用宽松阈值 2.0")
        return 2.0
    if any(any(keyword in theme for keyword in ["应用", "实际", "生活"]) for theme in resource["matched_themes"]):
        print("      🔍 V51.0应用题查询：使用宽松阈值 2.0")
        return 2.0
    if len(resource["matched_themes"]) > 1:
        print("      🔍 V48.0多主题匹配：使用宽松阈值 1.8")
        return 1.8
    return 1.5


def _print_match_summary(filtered_resources):
    multi_theme_resources = [r for r in filtered_resources if len(r["matched_themes"]) > 1]
    if multi_theme_resources:
        print(f"   ⭐ 发现 {len(multi_theme_resources)} 条多主题匹配资源:")
        for r in multi_theme_resources[:5]:
            print(f"      - {r['meta'].get('title', '未知标题')}: 匹配主题 {r['matched_themes']}")

    single_theme_resources = [r for r in filtered_resources if len(r["matched_themes"]) == 1]
    if single_theme_resources:
        print(f"   📋 发现 {len(single_theme_resources)} 条单主题匹配资源:")
        for r in single_theme_resources[:5]:
            theme = r["matched_themes"][0]
            distance = r["theme_distances"][theme]
            print(f"      - {r['meta'].get('title', '未知标题')}: 匹配主题 {theme} (距离: {distance:.4f})")
