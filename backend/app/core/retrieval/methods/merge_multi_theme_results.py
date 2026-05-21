from .._shared import *
from ..merge_helpers.collect import analyze_query_modes, collect_seen_resources
from ..merge_helpers.finalize import build_merged_result, sort_and_filter_resources, sort_separate_results


class _MergeMultiThemeResultsMixin:
    def _merge_multi_theme_results(self, all_results: List[Tuple[str, Dict[str, Any]]], is_separate_query: bool = False) -> Dict[str, Any]:
        """
        合并多个主题的检索结果

        Args:
            all_results: 所有主题的检索结果列表
            is_separate_query: 是否为分别查询（每个主题分别排序展示）
        """
        print(f"\n🔄 开始合并 {len(all_results)} 个主题的检索结果...")
        merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        all_themes, is_comparison_query, is_function_property_query, is_separate = analyze_query_modes(self, all_results)
        print(f"   📋 所有查询主题: {all_themes}")

        seen_resources = collect_seen_resources(self, all_results, all_themes, is_comparison_query, is_function_property_query, is_separate_query)
        filtered_resources = sort_and_filter_resources(self, seen_resources, all_themes, is_comparison_query)
        if not filtered_resources:
            return merged

        # 如果是分别查询，使用分别排序逻辑
        if is_separate_query or is_separate:
            print(f"\n✨ 分别查询模式：每个主题分别排序展示")
            return build_separate_merged_result(self, filtered_resources, all_themes)

        return build_merged_result(self, filtered_resources)


def build_separate_merged_result(retriever, filtered_resources, all_themes):
    """
    分别查询的合并结果构建：每个主题分别取最好的资源

    Args:
        retriever: 检索器实例
        filtered_resources: 过滤后的资源列表
        all_themes: 所有查询主题列表

    Returns:
        合并后的结果
    """
    print(f"\n✨ 构建分别查询结果：确保每个主题都有展示机会")

    # 按主题分组资源
    theme_resources = {theme: [] for theme in all_themes}
    other_resources = []

    for resource in filtered_resources:
        matched_themes = resource.get("matched_themes", [])
        if matched_themes:
            # 为每个匹配的主题都添加资源
            for theme in matched_themes:
                theme_dist = resource["theme_distances"].get(theme, float('inf'))
                theme_resources[theme].append((theme_dist, resource))
        else:
            # 无主题匹配的资源
            other_resources.append(resource)

    # 每个主题分别排序并取前N个
    max_per_theme = 5  # 每个主题最多展示5个
    final_resources = []

    print(f"   📊 分别排序结果：")
    for theme in all_themes:
        resources = theme_resources.get(theme, [])
        resources.sort(key=lambda x: x[0])  # 按距离排序
        selected = resources[:max_per_theme]
        for dist, resource in selected:
            final_resources.append(resource)
        print(f"      主题 '{theme}': 选取 {len(selected)} 个资源")

    # 多主题匹配的资源添加到最后
    for resource in other_resources:
        final_resources.append(resource)

    # 构建结果
    merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for resource in final_resources:
        meta_with_themes = resource["meta"].copy()
        meta_with_themes["_matched_themes"] = resource["matched_themes"]
        meta_with_themes["_theme_distances"] = resource["theme_distances"]
        meta_with_themes["_matched_theme_count"] = len(resource["matched_themes"])
        merged["documents"][0].append(resource["doc"])
        merged["metadatas"][0].append(meta_with_themes)
        merged["distances"][0].append(resource["dist"])
        merged["ids"][0].append(resource["id"])

    print(f"✅ 分别查询合并完成，共 {len(merged['documents'][0])} 条结果")

    # 应用数量限制
    if hasattr(retriever, '_current_quantity_limit') and retriever._current_quantity_limit:
        limit = retriever._current_quantity_limit
        print(f"🔍 应用数量限制：{limit} 条结果")
        for key in merged:
            if isinstance(merged[key], list) and merged[key]:
                merged[key][0] = merged[key][0][:limit]
        print(f"✅ 数量限制应用完成，保留 {len(merged['documents'][0])} 条结果")

    _print_separate_summary(final_resources, all_themes)
    return merged


def _print_separate_summary(filtered_resources, all_themes):
    """打印分别查询的结果摘要"""
    theme_resources = {theme: [] for theme in all_themes}
    for resource in filtered_resources:
        for theme in resource.get("matched_themes", []):
            if theme in theme_resources:
                theme_resources[theme].append(resource)

    print(f"\n📊 分别查询结果摘要：")
    for theme in all_themes:
        resources = theme_resources.get(theme, [])
        print(f"   主题 '{theme}': {len(resources)} 个资源")
        for r in resources[:3]:
            print(f"      - {r['meta'].get('title', '未知标题')}")
