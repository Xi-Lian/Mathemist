from .._shared import *


def analyze_query_modes(retriever, all_results):
    is_comparison_query = False
    is_separate_query = False
    themes = [theme for theme, _ in all_results]
    if len(all_results) >= 2:
        if hasattr(retriever, "_current_query_features") and retriever._current_query_features:
            query = retriever._current_query_features.get("original_query", "")
            if any(keyword in query for keyword in ["对比", "比较", "区别", "联系"]):
                is_comparison_query = True
                print(f"   🔍 V47.0检测到对比查询: {themes}")
            elif any(keyword in query for keyword in ["分别", "各自", "分开"]):
                is_separate_query = True
                print(f"   🔍 检测到分别查询: {themes}")
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
    return themes, is_comparison_query, is_function_property_query, is_separate_query


def _check_multi_field_match(doc, meta, theme, is_content_required=False):
    """
    多字段文本匹配（根据字段重要性分层）

    Args:
        doc: 文档内容
        meta: 文档元数据
        theme: 要匹配的主题
        is_content_required: 用户是否对内容有具体要求

    Returns:
        (是否匹配, 匹配类型, 匹配质量) 元组
    """
    # 特殊处理函数类主题，确保精确匹配
    function_themes = ["二次函数", "指数函数", "对数函数", "三角函数", "幂函数", "一次函数", "反比例函数"]
    is_function_theme = any(theme in ft for ft in function_themes)
    
    # 1. 文件名（最重要）
    title = meta.get("title", "")
    if theme in title:
        # 对于函数类主题，确保是精确匹配，不是部分匹配
        if is_function_theme:
            # 检查是否是完整的函数名称，而不是部分匹配
            import re
            # 创建正则表达式，匹配完整的函数名称
            pattern = r'\b' + re.escape(theme) + r'\b'
            if re.search(pattern, title):
                return True, "文件名", "high"
        else:
            return True, "文件名", "high"

    # 2. 完整路径（包含目录信息）
    source_file = meta.get("source_file", "") or meta.get("完整路径", "")
    if theme in source_file:
        # 对于函数类主题，确保是精确匹配
        if is_function_theme:
            import re
            pattern = r'\b' + re.escape(theme) + r'\b'
            if re.search(pattern, source_file):
                return True, "路径", "high"
        else:
            return True, "路径", "high"

    # 3. 知识点标签
    knowledge_tags = meta.get("知识点", "") or meta.get("知识点标签", "")
    if theme in knowledge_tags:
        return True, "知识点", "medium"

    # 4. 备注
    remarks = meta.get("备注", "")
    if theme in remarks:
        return True, "备注", "medium"

    # 5. 内容（根据用户是否有内容要求来决定权重）
    if theme in doc:
        # 对于函数类主题，确保是精确匹配
        if is_function_theme:
            import re
            pattern = r'\b' + re.escape(theme) + r'\b'
            if re.search(pattern, doc):
                if is_content_required:
                    return True, "内容", "high"
                else:
                    return True, "内容", "low"
        else:
            if is_content_required:
                return True, "内容", "high"
            else:
                return True, "内容", "low"

    return False, None, None


def collect_seen_resources(retriever, all_results, all_themes, is_comparison_query, is_function_property_query, is_separate_query=False):
    # 获取用户是否对内容有要求
    is_content_required = False
    if hasattr(retriever, "_current_query_features") and retriever._current_query_features:
        is_content_required = retriever._current_query_features.get("content_requirement", False)
        print(f"   🔍 content_requirement: {is_content_required}")

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
            threshold = _get_collect_threshold(meta.get("resource_type", ""), theme, len(all_themes), is_comparison_query, is_function_property_query)

            # 如果向量距离在阈值内，正常处理
            if dist < threshold:
                if not _passes_exclusion(retriever, meta, doc, theme, all_themes):
                    continue
                _record_resource_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query, is_content_required)
            else:
                # 向量距离超过阈值，尝试文本匹配
                matched, match_type, match_quality = _check_multi_field_match(doc, meta, theme, is_content_required)
                if matched:
                    # 文本匹配成功，检查排除词
                    if not _passes_exclusion(retriever, meta, doc, theme, all_themes):
                        continue
                    # 即使向量距离大，只要文本匹配成功（特别是文件名），也应该保留
                    _record_resource_match_with_text_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query, is_content_required, match_type, match_quality)
                else:
                    print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与主题 '{theme}' 向量距离不足 (距离: {dist:.3f} >= {threshold})，文本也不匹配，跳过")

    return seen_resources


def _record_resource_match_with_text_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query, is_content_required, match_type, match_quality):
    """
    当文本匹配成功时记录资源（即使向量距离较大）
    """
    unique_key = f"{meta.get('source_file', '')}_{meta.get('title', '')}"
    if unique_key not in seen_resources:
        seen_resources[unique_key] = {
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": id_,
            "matched_themes": [theme],
            "theme_distances": {theme: dist},
            "match_quality": {theme: match_quality}
        }
        print(f"      ✅ 文本匹配成功 '{meta.get('title', '未知')}' 匹配主题 '{theme}' ({match_type}, {match_quality}, 距离: {dist:.3f})")
        return

    if theme not in seen_resources[unique_key]["matched_themes"]:
        seen_resources[unique_key]["matched_themes"].append(theme)
        seen_resources[unique_key]["theme_distances"][theme] = dist
        seen_resources[unique_key]["match_quality"][theme] = match_quality
        print(f"      ➕ 文本匹配成功 '{meta.get('title', '未知')}' 新增匹配主题 '{theme}' ({match_type}, {match_quality}, 距离: {dist:.3f})")
    else:
        print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 已匹配主题 '{theme}'")

    existing_meta = seen_resources[unique_key]["meta"]
    for key in ["resource_type", "title", "source_file"]:
        if (key not in existing_meta or not existing_meta[key]) and key in meta and meta[key]:
            existing_meta[key] = meta[key]


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
        base_threshold = 1.0 if num_themes > 1 else 1.0
        if num_themes > 1:
            print(f"   🔍 V100.0多主题查询：使用标准阈值 {base_threshold}")
    return base_threshold


def _passes_exclusion(retriever, meta, doc, theme, all_themes):
    exclusion_factor = retriever._calculate_exclusion_factor(theme, meta.get("title", ""), doc, all_themes)
    if exclusion_factor == 0.0:
        print(f"      ⚠️ 排除：'{meta.get('title', '未知')}' 包含排除词 (主题: {theme})")
        return False
    if meta.get("resource_type", "") == "exercise":
        print(f"      ✅ 习题资源通过排除词检查: '{meta.get('title', '未知')}' (主题: {theme})")
    return True


def _record_resource_match(seen_resources, meta, doc, dist, id_, theme, is_function_property_query, is_content_required=False):
    unique_key = f"{meta.get('source_file', '')}_{meta.get('title', '')}"
    
    # 检查是否为函数类主题
    function_themes = ["二次函数", "指数函数", "对数函数", "三角函数", "幂函数", "一次函数", "反比例函数"]
    is_function_theme = any(theme in ft for ft in function_themes)
    
    # 检查是否为教案或课件资源
    resource_type = meta.get("resource_type", "")
    is_lesson_plan = resource_type == "lesson_plan" or any(keyword in (resource_type + meta.get('title', '') + meta.get('source_file', '')) for keyword in ["教案", "教学设计"])
    is_courseware = resource_type == "courseware" or any(keyword in (resource_type + meta.get('title', '') + meta.get('source_file', '')) for keyword in ["课件", "PPT", "幻灯片"])
    
    if unique_key not in seen_resources:
        # 对于教案和课件资源，即使是非函数类主题，也不要求文本匹配
        if not is_function_theme and not (is_lesson_plan or is_courseware):
            matched, match_type, match_quality = _check_multi_field_match(doc, meta, theme, is_content_required)
            if not matched:
                print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与非函数类主题 '{theme}' 文本不匹配，跳过")
                return
        
        seen_resources[unique_key] = {
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": id_,
            "matched_themes": [theme],
            "theme_distances": {theme: dist},
            "match_quality": {}
        }
        print(f"      ✅ 新资源 '{meta.get('title', '未知')}' 匹配主题 '{theme}' (距离: {dist:.3f})")
        return

    if theme not in seen_resources[unique_key]["matched_themes"]:
        # 为多主题查询使用更宽松的阈值
        if is_lesson_plan or is_courseware:
            # 教案和课件资源使用宽松阈值
            similarity_threshold = 2.5
        elif is_function_property_query:
            similarity_threshold = 1.0
        else:
            # 多主题查询使用更宽松的阈值
            similarity_threshold = 1.8
        
        if dist < similarity_threshold:
            # 对于教案和课件资源，即使是非函数类主题，也不要求文本匹配
            if not is_function_theme and not (is_lesson_plan or is_courseware):
                matched, match_type, match_quality = _check_multi_field_match(doc, meta, theme, is_content_required)
                if not matched:
                    print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与非函数类主题 '{theme}' 文本不匹配，不添加匹配")
                    return
            
            seen_resources[unique_key]["matched_themes"].append(theme)
            seen_resources[unique_key]["theme_distances"][theme] = dist
            print(f"      ➕ 资源 '{meta.get('title', '未知')}' 新增匹配主题 '{theme}' (距离: {dist:.3f})")
        else:
            # 当向量距离不够时，尝试文本匹配
            matched, match_type, match_quality = _check_multi_field_match(doc, meta, theme, is_content_required)
            if matched:
                seen_resources[unique_key]["matched_themes"].append(theme)
                seen_resources[unique_key]["theme_distances"][theme] = dist
                seen_resources[unique_key]["match_quality"][theme] = match_quality
                print(f"      ➕ 资源 '{meta.get('title', '未知')}' 文本匹配主题 '{theme}' ({match_type}, {match_quality})")
            else:
                print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与主题 '{theme}' 相似度不足 (距离: {dist:.3f} >= {similarity_threshold})，文本也不匹配，不添加匹配")
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
