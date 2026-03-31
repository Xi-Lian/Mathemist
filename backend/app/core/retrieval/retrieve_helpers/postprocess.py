from .._shared import *


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


def apply_quantity_limit(results, quantity_limit, core_theme):
    if not quantity_limit or len(results["documents"][0]) <= quantity_limit:
        return results

    core_theme_resources = []
    other_resources = []
    for i, meta in enumerate(results["metadatas"][0]):
        contains_core_theme = False
        if core_theme:
            content = results["documents"][0][i] or ""
            title = meta.get("title", "") or ""
            metadata_str = str(meta) or ""
            contains_core_theme = core_theme in content or core_theme in title or core_theme in metadata_str
        if contains_core_theme:
            core_theme_resources.append(i)
        else:
            other_resources.append(i)

    prioritized_indices = (core_theme_resources + other_resources)[:quantity_limit]
    prioritized_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for idx in prioritized_indices:
        prioritized_results["documents"][0].append(results["documents"][0][idx])
        prioritized_results["metadatas"][0].append(results["metadatas"][0][idx])
        prioritized_results["distances"][0].append(results["distances"][0][idx])
        prioritized_results["ids"][0].append(results["ids"][0][idx])

    print(f"🔍 V33.0应用数量限制: {quantity_limit}")
    print(f"     ✅ V33.0数量限制应用完成，返回 {len(prioritized_results['documents'][0])} 条结果")
    print(f"     ✅ 其中包含核心主题的资源: {min(len(core_theme_resources), quantity_limit)} 条")
    return prioritized_results


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
