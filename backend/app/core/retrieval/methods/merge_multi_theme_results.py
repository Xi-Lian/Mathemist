from .._shared import *
from ..merge_helpers.collect import analyze_query_modes, collect_seen_resources
from ..merge_helpers.finalize import build_merged_result, sort_and_filter_resources


class _MergeMultiThemeResultsMixin:
    def _merge_multi_theme_results(self, all_results: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        合并多个主题的检索结果
        """
        print(f"\n🔄 开始合并 {len(all_results)} 个主题的检索结果...")
        merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        all_themes, is_comparison_query, is_function_property_query = analyze_query_modes(self, all_results)
        print(f"   📋 所有查询主题: {all_themes}")

        seen_resources = collect_seen_resources(all_results, all_themes, is_comparison_query, is_function_property_query)
        filtered_resources = sort_and_filter_resources(self, seen_resources, all_themes, is_comparison_query)
        if not filtered_resources:
            return merged
        return build_merged_result(self, filtered_resources)
