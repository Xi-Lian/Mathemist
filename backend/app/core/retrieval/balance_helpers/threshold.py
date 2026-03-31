from .._shared import *


def apply_relevance_gap_filter(resources_sorted):
    if len(resources_sorted) <= 1:
        return resources_sorted

    max_relevance = resources_sorted[0].get("relevance", 0)
    if max_relevance > 0.80:
        dynamic_threshold = max_relevance * 0.50
    elif max_relevance > 0.60:
        dynamic_threshold = max_relevance * 0.45
    elif max_relevance > 0.40:
        dynamic_threshold = max_relevance * 0.40
    elif max_relevance > 0.20:
        dynamic_threshold = max_relevance * 0.35
    else:
        dynamic_threshold = max_relevance * 0.30

    threshold = max(dynamic_threshold, 0.15)
    print(f"   📊 V14.3动态阈值：最高相关性{max_relevance:.1%}，阈值{threshold:.1%}")

    gaps = []
    for i in range(len(resources_sorted) - 1):
        gap = resources_sorted[i].get("relevance", 0) - resources_sorted[i + 1].get("relevance", 0)
        gaps.append((i, gap))

    significant_gaps = [(i, gap) for i, gap in gaps if gap > threshold]
    if significant_gaps:
        first_gap_idx = significant_gaps[0][0]
        print(f"   📊 V14.1检测到相关性断层：位置{first_gap_idx}，差距{significant_gaps[0][1]:.1%}")
        print(f"   📊 断层前相关性：{resources_sorted[first_gap_idx].get('relevance', 0):.1%}")
        print(f"   📊 断层后相关性：{resources_sorted[first_gap_idx + 1].get('relevance', 0):.1%}")
        high_relevance_resources = resources_sorted[: first_gap_idx + 1]
        print(f"   ✅ V14.1只保留高相关性资源：{len(high_relevance_resources)}个（原{len(resources_sorted)}个）")
        high_relevance_resources.sort(
            key=lambda x: (-x.get("priority_score", 0), -x.get("is_core_match", False), -x.get("relevance", 0), -x.get("matched_theme_count", 0), -x.get("theme_boost", 0))
        )
        return high_relevance_resources

    if max_relevance > 0.80:
        min_relevance_threshold = max_relevance * 0.50
    elif max_relevance > 0.60:
        min_relevance_threshold = max_relevance * 0.45
    elif max_relevance > 0.40:
        min_relevance_threshold = max_relevance * 0.40
    else:
        min_relevance_threshold = max_relevance * 0.35

    min_relevance_threshold = max(min_relevance_threshold, 0.30)
    filtered_resources = [r for r in resources_sorted if r.get("relevance", 0) >= min_relevance_threshold]
    if len(filtered_resources) < len(resources_sorted):
        print(f"   ✅ V14.1过滤低相关性资源：保留{len(filtered_resources)}个（原{len(resources_sorted)}个），阈值{min_relevance_threshold:.1%}")
        filtered_resources.sort(
            key=lambda x: (-x.get("priority_score", 0), -x.get("is_core_match", False), -x.get("relevance", 0), -x.get("matched_theme_count", 0), -x.get("theme_boost", 0))
        )
        return filtered_resources

    return resources_sorted
