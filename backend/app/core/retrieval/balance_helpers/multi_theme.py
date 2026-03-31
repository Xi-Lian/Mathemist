from .._shared import *


def balance_multi_theme_resources(retriever, resources_sorted, core_themes):
    print(f"   🔄 多主题资源分布平衡，主题: {core_themes}")
    theme_resources = {theme: [] for theme in core_themes}
    other_resources = []
    print(f"   🔍 多主题资源分布平衡：filtered_resources 数量: {len(resources_sorted)}")

    is_function_property_query = any(theme in ["函数的单调性", "函数的奇偶性", "函数的周期性"] for theme in core_themes)
    for resource in resources_sorted:
        assigned_themes = _assign_resource_to_themes(resource, core_themes, theme_resources, is_function_property_query)
        if not assigned_themes:
            other_resources.append(resource)
            print("      ⚠️ 未分配到任何主题")

    theme_counts = {theme: len(resources) for theme, resources in theme_resources.items()}
    print(f"   📊 各主题资源数量: {theme_counts}")

    _supplement_theme_resources(resources_sorted, core_themes, theme_resources, other_resources, is_function_property_query)
    theme_counts = {theme: len(resources) for theme, resources in theme_resources.items()}
    print(f"   📊 补充后各主题资源数量: {theme_counts}")

    total_visible = len(resources_sorted)
    target_per_theme = max(3, int(total_visible / len(core_themes) * 1.5))
    print(f"   🎯 每个主题目标数量: {target_per_theme}")

    query_features = getattr(retriever, "_current_query_features", {})
    for theme in core_themes:
        theme_list = theme_resources[theme]
        if query_features.get("has_content_requirement"):
            print(f"   🔍 V9.1为主题 '{theme}' 计算内容匹配得分...")
            for resource in theme_list:
                if "content_features" in resource:
                    content_score = retriever.content_extractor.calculate_content_match_score(resource["content_features"], query_features)
                    original_relevance = resource.get("relevance", 0)
                    resource["relevance"] = original_relevance * 0.7 + content_score * 0.3
                    resource["content_match_score"] = content_score
                    resource["original_relevance"] = original_relevance

        theme_list.sort(key=lambda x: (-x.get("is_core_match", False), -x.get("relevance", 0), -x.get("matched_theme_count", 0), -x.get("theme_boost", 0)))
        print(f"   ✅ 主题 '{theme}': 共 {len(theme_list)} 个资源")

    balanced_resources = _round_robin_select(theme_resources, core_themes, total_visible, target_per_theme)
    if not balanced_resources:
        return []

    max_relevance = balanced_resources[0].get("relevance", 0)
    if max_relevance > 0.80:
        min_relevance_threshold = 0.50 * max_relevance
    elif max_relevance > 0.60:
        min_relevance_threshold = 0.40 * max_relevance
    elif max_relevance > 0.40:
        min_relevance_threshold = 0.30 * max_relevance
    else:
        min_relevance_threshold = 0.20 * max_relevance
    min_relevance_threshold = max(min_relevance_threshold, 0.20)

    filtered_balanced_resources = [r for r in balanced_resources if r.get("relevance", 0) >= min_relevance_threshold]
    filtered_other_resources = [r for r in other_resources if r.get("relevance", 0) >= min_relevance_threshold]
    remaining_space = max(0, total_visible - len(filtered_balanced_resources))
    max_other_count = max(0, int(total_visible * 0.33))
    other_count = min(len(filtered_other_resources), remaining_space, max_other_count)

    balanced_resources = filtered_balanced_resources + filtered_other_resources[:other_count]
    balanced_resources.sort(key=lambda x: x.get("relevance", 0), reverse=True)
    print(f"   ✅ 平衡完成: {len(balanced_resources)} 个资源（核心主题: {len(filtered_balanced_resources)}个，其他资源: {other_count}个，过滤后）")
    return balanced_resources


def _assign_resource_to_themes(resource, core_themes, theme_resources, is_function_property_query):
    matched_themes = resource.get("matched_themes", [])
    assigned_themes = []
    print(f"   🔍 检查资源 '{resource.get('title', '未知')}' 的 matched_themes: {matched_themes}")
    for theme in core_themes:
        if any(theme.strip() == t.strip() for t in matched_themes):
            theme_resources[theme].append(resource)
            assigned_themes.append(theme)
            print(f"      ✅ 分配到主题 '{theme}'")
        elif is_function_property_query and _matches_function_property_theme(resource, theme):
            theme_resources[theme].append(resource)
            assigned_themes.append(theme)
            print(f"      ✅ 函数性质宽松匹配：分配到主题 '{theme}'")
    return assigned_themes


def _supplement_theme_resources(resources_sorted, core_themes, theme_resources, other_resources, is_function_property_query):
    min_resources_per_theme = 2
    for theme in core_themes:
        if len(theme_resources[theme]) >= min_resources_per_theme:
            continue
        print(f"   ⚠️ 主题 '{theme}' 资源不足 ({len(theme_resources[theme])}个)，尝试从其他资源补充...")
        for resource in other_resources[:]:
            resource_content = resource.get("content", "") or resource.get("doc", "")
            if theme == "一次函数":
                linear_keywords = ["一次函数", "线性函数", "直线", "斜率", "截距", "正比例函数", "y=kx", "y = kx", "y=ax", "y = ax", "y=x", "y = x", "线性关系"]
                if any(keyword in resource_content for keyword in linear_keywords):
                    theme_resources[theme].append(resource)
                    other_resources.remove(resource)
                    print(f"      ✅ V23.2补充一次函数资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
            elif is_function_property_query and _matches_function_property_theme(resource, theme):
                theme_resources[theme].append(resource)
                other_resources.remove(resource)
                print(f"      ✅ 补充函数性质资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
            elif theme in resource_content:
                theme_resources[theme].append(resource)
                other_resources.remove(resource)
                print(f"      ✅ 补充资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")

            if len(theme_resources[theme]) >= min_resources_per_theme:
                break

    if "一次函数" in core_themes and len(theme_resources.get("一次函数", [])) < min_resources_per_theme:
        print("   ⚠️ V24.1: 一次函数资源仍然不足，从所有资源中强制补充...")
        for resource in resources_sorted[:]:
            if resource in theme_resources.get("一次函数", []):
                continue
            resource_content = resource.get("content", "") or resource.get("doc", "")
            knowledge_tags = resource.get("metadata", {}).get("知识点", "")
            if "一次函数" in knowledge_tags or "一次函数" in resource_content:
                theme_resources["一次函数"].append(resource)
                print(f"      ✅ V24.1强制补充一次函数资源: {resource.get('title', '未知')[:30]}...")
                if len(theme_resources["一次函数"]) >= min_resources_per_theme:
                    break


def _round_robin_select(theme_resources, core_themes, total_visible, target_per_theme):
    balanced_resources = []
    theme_indices = {theme: 0 for theme in core_themes}
    used_resources = set()
    round_num = 0

    while len(balanced_resources) < total_visible:
        added_in_round = 0
        for theme in core_themes:
            theme_list = theme_resources[theme]
            idx = theme_indices[theme]
            while idx < len(theme_list) and (idx < target_per_theme or len(balanced_resources) < len(core_themes)):
                resource = theme_list[idx]
                resource_id = f"{resource.get('title', '')}_{resource.get('source', '')}"
                if resource_id not in used_resources:
                    balanced_resources.append(resource)
                    used_resources.add(resource_id)
                    theme_indices[theme] = idx + 1
                    added_in_round += 1
                    print(f"      ✅ 轮询选择：主题 '{theme}' 资源 {idx + 1}: {resource.get('title', '未知')}")
                    break
                idx += 1
                theme_indices[theme] = idx
        if added_in_round == 0:
            break
        round_num += 1

    print(f"   🔄 轮询选择完成: {round_num} 轮，共选择 {len(balanced_resources)} 个资源")
    return balanced_resources


def _matches_function_property_theme(resource, theme):
    resource_content = resource.get("content", "") or resource.get("doc", "")
    resource_source = resource.get("source", "")
    knowledge_tags = resource.get("知识点", "") or resource.get("metadata", {}).get("知识点", "") or resource.get("metadata", {}).get("知识点标签", "")
    if theme == "函数的单调性":
        keywords = ["单调性", "单调", "增函数", "减函数", "单调递增", "单调递减"]
    elif theme == "函数的奇偶性":
        keywords = ["奇偶性", "奇函数", "偶函数", "对称性", "对称"]
    elif theme == "函数的周期性":
        keywords = ["周期性", "周期", "周期函数"]
    else:
        return False
    return any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in keywords)
