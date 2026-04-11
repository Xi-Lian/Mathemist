from .._shared import *
import re


FUNCTION_CONCEPT_KEYWORDS = [
    "函数的概念",
    "函数的性质",
    "函数的单调性",
    "函数的奇偶性",
    "函数的周期性",
    "函数的定义域",
    "函数的值域",
    "函数的图像",
    "函数的零点",
    "函数的应用",
]
GENERAL_MATERIAL_HINTS = ["资料", "学习资料", "教学资源", "教学资料", "资源", "内容"]
EXPLICIT_EXERCISE_HINTS = ["习题", "题目", "练习题", "练习", "测试题", "选择题", "填空题", "解答题", "证明题"]
SEMANTIC_RESOURCE_HINTS = [
    "教案",
    "教学设计",
    "教学方案",
    "课件",
    "PPT",
    "演示文稿",
    "教学大纲",
    "课程标准",
    "课例",
    "GGB",
]
SPECIFIC_THEME_GUARD_BROAD_THEMES = {
    "函数",
    "数学",
    "代数",
    "几何",
    "统计",
    "概率",
    "函数的概念",
    "函数的性质",
    "函数应用",
}
QUERY_NOISE_TERMS = {
    "推荐", "几道", "给我", "找", "一些", "几个", "来几道", "来一些", "要几道",
    "习题", "题目", "练习题", "练习", "测试题", "选择题", "填空题", "解答题", "证明题",
    "推荐几道", "帮我", "一下", "相关", "关于",
}


def _normalize_match_text(text):
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("的", "")
    normalized = re.sub(r"[\s,，。；;、:：()\[\]（）\-_/]+", "", normalized)
    return normalized


def apply_difficulty_filter(results, difficulty_info, quantity_limit):
    if not difficulty_info:
        return results

    print(f"🔍 V92.0应用难度筛选: {difficulty_info}")
    difficulty_level = difficulty_info.get("difficulty", "")
    if not difficulty_level:
        if quantity_limit and len(results["documents"][0]) < quantity_limit:
            print(f"     ⚠️ V95.0资源不足，放宽难度限制（当前: {len(results['documents'][0])} 条, 要求: {quantity_limit} 条）")
            print(f"     ✅ V95.0保留所有结果，数量: {len(results['documents'][0])}")
        return results

    filtered_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for i, meta in enumerate(results["metadatas"][0]):
        resource_difficulty = meta.get("难度（1-5）", 3)
        if resource_difficulty in (None, ""):
            resource_difficulty = meta.get("难度", 3)
        try:
            resource_difficulty = int(resource_difficulty)
        except (ValueError, TypeError):
            resource_difficulty = 3

        if _matches_difficulty(difficulty_level, resource_difficulty, meta):
            filtered_results["documents"][0].append(results["documents"][0][i])
            filtered_results["metadatas"][0].append(meta)
            filtered_results["distances"][0].append(results["distances"][0][i])
            filtered_results["ids"][0].append(results["ids"][0][i])

    if filtered_results["documents"][0]:
        print(f"     ✅ V92.0难度筛选完成，保留 {len(filtered_results['documents'][0])} 条结果")
        return filtered_results

    print("     ⚠️ V92.0难度筛选后无结果，返回原始结果")
    return results


def apply_question_type_filter(results, question_type, quantity_limit):
    if not question_type:
        return results

    print(f"🔍 V92.0应用题目类型筛选: {question_type}")
    print(f"   🔍 V92.0调试 - 原始结果数量: {len(results['documents'][0])}")
    filtered_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    exercise_count = 0
    other_count = 0

    for i, meta in enumerate(results["metadatas"][0]):
        db_resource_type = meta.get("resource_type", "")
        if db_resource_type == "exercise":
            if _matches_question_type(question_type, meta):
                filtered_results["documents"][0].append(results["documents"][0][i])
                filtered_results["metadatas"][0].append(meta)
                filtered_results["distances"][0].append(results["distances"][0][i])
                filtered_results["ids"][0].append(results["ids"][0][i])
                exercise_count += 1
        else:
            filtered_results["documents"][0].append(results["documents"][0][i])
            filtered_results["metadatas"][0].append(meta)
            filtered_results["distances"][0].append(results["distances"][0][i])
            filtered_results["ids"][0].append(results["ids"][0][i])
            other_count += 1

    print(f"   🔍 V92.0调试 - 保留习题: {exercise_count}条, 其他资源: {other_count}条")
    if filtered_results["documents"][0]:
        print(f"     ✅ V92.0题目类型筛选完成，保留 {len(filtered_results['documents'][0])} 条结果")
        return filtered_results

    if quantity_limit:
        print(f"     ⚠️ V95.0题目类型筛选后无结果，返回原始结果（数量限制: {quantity_limit}）")
    else:
        print("     ⚠️ V92.0题目类型筛选后无结果，返回原始结果")
    return results


def prioritize_pure_function_results(retriever, query, results, quantity_limit):
    core_theme = retriever._extract_core_theme(query)
    specific_function_types = retriever.config_loader.get_all_function_types()
    is_pure_function_query = (core_theme == "函数" or "函数题" in query) and not any(
        func_type in query for func_type in specific_function_types
    )

    if not (is_pure_function_query and quantity_limit):
        return results

    print("🔍 V48.2纯函数查询预过滤: 优先保留函数概念、性质等资源")
    concept_property_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    other_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    for i, meta in enumerate(results["metadatas"][0]):
        source_file = meta.get("source_file", "")
        title = meta.get("title", "")
        content = results["documents"][0][i]
        is_concept_property = False

        if "必修一第三章" in source_file or "第三章-函数的概念" in source_file:
            is_concept_property = True
        elif any(keyword in f"{title} {content}" for keyword in FUNCTION_CONCEPT_KEYWORDS):
            is_concept_property = True

        bucket = concept_property_results if is_concept_property else other_results
        bucket["documents"][0].append(results["documents"][0][i])
        bucket["metadatas"][0].append(meta)
        bucket["distances"][0].append(results["distances"][0][i])
        bucket["ids"][0].append(results["ids"][0][i])

    print(f"     ✅ 函数概念性质资源: {len(concept_property_results['documents'][0])} 条")
    print(f"     ✅ 其他资源: {len(other_results['documents'][0])} 条")

    combined_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for key in combined_results:
        combined_results[key][0] = concept_property_results[key][0] + other_results[key][0]
    return combined_results


def _contains_any(text, keywords):
    return any(keyword in (text or "") for keyword in keywords)


def _is_general_material_query(query, resource_types):
    has_general = _contains_any(query, GENERAL_MATERIAL_HINTS) or any(
        rt in {"资料", "资源", "教学资源", "教学资料", "学习资料"} for rt in (resource_types or [])
    )
    return has_general and not _contains_any(query, EXPLICIT_EXERCISE_HINTS)


def _normalize_result_category(meta):
    source_file = meta.get("source_file", "") or ""
    resource_type = meta.get("resource_type", "") or ""
    title = meta.get("title", "") or ""
    text = f"{resource_type} {source_file} {title}"

    if "lesson_plan" in resource_type or "教案" in text:
        return "lesson_plan"
    if "courseware" in resource_type or any(keyword in text for keyword in ["课件", "PPT", "幻灯片", "演示文稿"]):
        return "courseware"
    if "syllabus" in resource_type or any(keyword in text for keyword in ["教学大纲", "课程标准", "大纲"]):
        return "syllabus"
    if "lesson_case" in resource_type or any(keyword in text for keyword in ["课例", "课堂实录", "教学视频"]):
        return "lesson_case"
    if "ggb" in resource_type or "geogebra" in text.lower():
        return "ggb"
    if "theory" in resource_type:
        return "theory"
    if "exercise" in resource_type or "习题" in text:
        return "exercise"
    return "general"


def _raw_theme_score(core_theme, meta, doc):
    if not core_theme:
        return 0.0

    title = meta.get("title", "") or ""
    source_file = meta.get("source_file", "") or ""
    knowledge_tags = meta.get("知识点", "") or meta.get("知识点标签", "") or ""
    normalized_theme = _normalize_match_text(core_theme)
    title_norm = _normalize_match_text(title)
    source_norm = _normalize_match_text(source_file)
    knowledge_norm = _normalize_match_text(knowledge_tags)
    text = _normalize_match_text(f"{title} {source_file} {knowledge_tags} {doc or ''}")

    if normalized_theme in title_norm:
        return 1.0
    if normalized_theme in source_norm:
        return 0.9
    if normalized_theme in knowledge_norm:
        return 0.85
    if normalized_theme in text:
        return 0.7
    return 0.0


def _extract_query_terms(query, core_theme):
    text = query or ""
    for hint in EXPLICIT_EXERCISE_HINTS + GENERAL_MATERIAL_HINTS + list(QUERY_NOISE_TERMS):
        text = text.replace(hint, " ")
    parts = [part.strip() for part in re.split(r"[\s,，。；、]+", text) if len(part.strip()) >= 2]

    expanded_terms = []
    for part in parts:
        expanded_terms.append(part)
        if "正弦函数" in part and "正弦函数" not in expanded_terms:
            expanded_terms.append("正弦函数")
        if "余弦函数" in part and "余弦函数" not in expanded_terms:
            expanded_terms.append("余弦函数")
        if "图象" in part and "图象" not in expanded_terms:
            expanded_terms.append("图象")
        if "图像" in part and "图像" not in expanded_terms:
            expanded_terms.append("图像")

    unique_terms = []
    seen = set()
    for term in expanded_terms:
        if term and term != core_theme and term not in seen:
            seen.add(term)
            unique_terms.append(term)
    return unique_terms


def _specific_query_score(query, core_theme, meta, doc):
    terms = _extract_query_terms(query, core_theme)
    if not terms:
        return 0.0

    title = meta.get("title", "") or ""
    source_file = meta.get("source_file", "") or ""
    knowledge_tags = meta.get("知识点", "") or meta.get("知识点标签", "") or ""
    title_norm = _normalize_match_text(title)
    source_norm = _normalize_match_text(source_file)
    knowledge_norm = _normalize_match_text(knowledge_tags)
    haystack = _normalize_match_text(f"{title} {source_file} {knowledge_tags} {doc or ''}")

    score = 0.0
    for term in terms:
        normalized_term = _normalize_match_text(term)
        if not normalized_term:
            continue
        if normalized_term in title_norm:
            score += 1.0
        elif normalized_term in source_norm:
            score += 0.9
        elif normalized_term in knowledge_norm:
            score += 0.75
        elif normalized_term in haystack:
            score += 0.4
    return score


def _build_diverse_indices(results, quantity_limit, core_theme):
    buckets = {
        "theory": [],
        "lesson_plan": [],
        "courseware": [],
        "syllabus": [],
        "lesson_case": [],
        "ggb": [],
        "exercise": [],
        "general": [],
    }

    for i, meta in enumerate(results["metadatas"][0]):
        category = _normalize_result_category(meta)
        score = _raw_theme_score(core_theme, meta, results["documents"][0][i])
        buckets.setdefault(category, []).append((score, i))

    for category, items in buckets.items():
        items.sort(key=lambda item: (-item[0], item[1]))

    prioritized = []
    preferred_order = ["theory", "lesson_plan", "courseware", "syllabus", "lesson_case", "ggb", "general", "exercise"]

    # 第一轮每类先拿一个，避免资料查询在预截断阶段被单一类型吞掉。
    for category in preferred_order:
        if buckets.get(category):
            prioritized.append(buckets[category].pop(0)[1])
            if len(prioritized) >= quantity_limit:
                return prioritized

    exercise_cap = max(2, quantity_limit // 4)
    exercise_taken = 0
    for category in preferred_order:
        for _, idx in buckets.get(category, []):
            if category == "exercise" and exercise_taken >= exercise_cap:
                continue
            prioritized.append(idx)
            if category == "exercise":
                exercise_taken += 1
            if len(prioritized) >= quantity_limit:
                return prioritized

    return prioritized[:quantity_limit]


def apply_quantity_limit(results, quantity_limit, core_theme, query="", resource_types=None):
    if not quantity_limit or len(results["documents"][0]) <= quantity_limit:
        return results

    if _is_general_material_query(query, resource_types):
        prioritized_indices = _build_diverse_indices(results, quantity_limit, core_theme)
        prioritized_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        for idx in prioritized_indices:
            prioritized_results["documents"][0].append(results["documents"][0][idx])
            prioritized_results["metadatas"][0].append(results["metadatas"][0][idx])
            prioritized_results["distances"][0].append(results["distances"][0][idx])
            prioritized_results["ids"][0].append(results["ids"][0][idx])

        print(f"🔍 资料查询预截断改为多类型保留: {quantity_limit}")
        print(f"     ✅ 预留类型数: {len({_normalize_result_category(results['metadatas'][0][idx]) for idx in prioritized_indices})}")
        return prioritized_results

    scored_indices = []
    for i, meta in enumerate(results["metadatas"][0]):
        contains_core_theme = False
        if core_theme:
            content = _normalize_match_text(results["documents"][0][i] or "")
            title = _normalize_match_text(meta.get("title", "") or "")
            metadata_str = _normalize_match_text(str(meta) or "")
            normalized_theme = _normalize_match_text(core_theme)
            contains_core_theme = normalized_theme in content or normalized_theme in title or normalized_theme in metadata_str
        scored_indices.append((
            i,
            1 if contains_core_theme else 0,
            _specific_query_score(query, core_theme, meta, results["documents"][0][i]),
            -(results["distances"][0][i] if results["distances"][0][i] is not None else 99.0),
        ))

    scored_indices.sort(key=lambda item: (-item[2], -item[1], -item[3], item[0]))
    prioritized_indices = [item[0] for item in scored_indices[:quantity_limit]]
    core_theme_count = sum(item[1] for item in scored_indices[:quantity_limit])
    prioritized_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for idx in prioritized_indices:
        prioritized_results["documents"][0].append(results["documents"][0][idx])
        prioritized_results["metadatas"][0].append(results["metadatas"][0][idx])
        prioritized_results["distances"][0].append(results["distances"][0][idx])
        prioritized_results["ids"][0].append(results["ids"][0][idx])

    print(f"🔍 V33.0应用数量限制: {quantity_limit}")
    print(f"     ✅ V33.0数量限制应用完成，返回 {len(prioritized_results['documents'][0])} 条结果")
    print(f"     ✅ 其中包含核心主题的资源: {core_theme_count} 条")
    return prioritized_results


def enforce_specific_theme_precision(classified_resources, core_theme):
    themes = [theme.strip() for theme in (core_theme or "").split(",") if theme.strip()]
    if not themes or not any(theme not in SPECIFIC_THEME_GUARD_BROAD_THEMES for theme in themes):
        return classified_resources

    rebuilt = {}
    kept_count = 0
    removed_count = 0

    for key, value in classified_resources.items():
        if not isinstance(value, list) or key.startswith("_"):
            rebuilt[key] = value
            continue

        kept_resources = []
        for resource in value:
            if not isinstance(resource, dict):
                continue
            if _resource_matches_specific_theme(resource, themes):
                kept_resources.append(resource)
            else:
                removed_count += 1
        rebuilt[key] = kept_resources
        kept_count += len(kept_resources)

    rebuilt["_precision_guard"] = {
        "applied": True,
        "core_theme": ",".join(themes),
        "kept_count": kept_count,
        "removed_count": removed_count,
    }
    return rebuilt


def _resource_matches_specific_theme(resource, themes):
    if resource.get("is_core_match"):
        return True

    matched_themes = resource.get("matched_themes", []) or []
    related_themes = resource.get("related_themes", []) or []
    mentioned_themes = resource.get("mentioned_themes", []) or []
    if any(theme in matched_themes or theme in related_themes or theme in mentioned_themes for theme in themes):
        return True

    title = resource.get("title", "") or ""
    content = resource.get("content", "") or ""
    source = resource.get("source", "") or ""
    knowledge = resource.get("知识点", "") or ""
    metadata = resource.get("metadata", {}) if isinstance(resource.get("metadata"), dict) else {}
    knowledge_tags = metadata.get("知识点标签", "") or metadata.get("知识点", "") or ""
    haystack = _normalize_match_text(f"{title} {content} {source} {knowledge} {knowledge_tags}")
    return any(_normalize_match_text(theme) in haystack for theme in themes)


def _matches_difficulty(difficulty_level, resource_difficulty, meta):
    if difficulty_level == "基础":
        return resource_difficulty <= 2
    if difficulty_level == "中等":
        return 2 <= resource_difficulty <= 3
    if difficulty_level in {"困难", "难"}:
        return resource_difficulty >= 3
    if difficulty_level == "综合":
        knowledge_tags = meta.get("知识点标签", "")
        has_multiple_topics = len(knowledge_tags.split(";")) >= 2 if knowledge_tags else False
        title_and_stem = meta.get("title", "") + meta.get("题干", "")
        has_application = any(kw in title_and_stem for kw in ["应用", "实际", "利润", "面积", "模型", "建模"])
        return has_multiple_topics or has_application
    return False


def _matches_question_type(question_type, meta):
    question_type_field = meta.get("题目类型", "")
    question_content = meta.get("题干", "")
    if question_type == "选择题":
        return (
            "选择题" in question_type_field
            or "单选" in question_type_field
            or "多选" in question_type_field
            or any(kw in question_content for kw in ["A.", "B.", "C.", "D.", "A、", "B、", "C、", "D、", "（A）", "（B）", "（C）", "（D）"])
        )
    if question_type == "填空题":
        return (
            "填空题" in question_type_field
            or "填空" in question_type_field
            or any(kw in question_content for kw in ["______", "_____", "____", "___", "__", "（    ）", "（   ）", "（  ）", "（ ）"])
        )
    if question_type == "解答题":
        return (
            "解答题" in question_type_field
            or "计算题" in question_type_field
            or "应用题" in question_type_field
            or any(kw in question_content for kw in ["解：", "证明：", "求：", "计算：", "求解", "证明", "解答", "计算"])
        )
    if question_type == "证明题":
        return (
            "证明题" in question_type_field
            or "证明" in question_type_field
            or any(kw in question_content for kw in ["证明：", "求证：", "证明", "求证", "∵", "∴"])
        )
    return False
