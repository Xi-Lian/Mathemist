from .._shared import *


def calculate_relevance_boost(retriever, classified, metadata, doc, distance, resource_type, resource_types, core_theme, query, question_type, grade, difficulty):
    current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
    relevance = max(0.0, 1.0 - (distance / 2)) if distance is not None else 0.5

    knowledge_match_score = 0.0
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "") or ""
    if core_theme and knowledge_tags:
        themes = [t.strip() for t in core_theme.split(",") if t.strip()]
        for theme in themes:
            if theme in knowledge_tags:
                knowledge_match_score += 0.3
                break
        for theme in themes:
            if theme in retriever.knowledge_hierarchy:
                keywords = retriever.knowledge_hierarchy[theme].get("keywords", [])
                for keyword in keywords:
                    if keyword in knowledge_tags:
                        knowledge_match_score += 0.2
                        break

    type_match_score = 0.0
    if resource_types:
        for user_type in resource_types:
            mapping = get_resource_type_mapping(user_type)
            if mapping:
                standard_name, db_type = mapping
                if resource_type in {db_type, user_type, standard_name}:
                    type_match_score = 0.2
                    break

    question_type_match_score = 0.0
    if resource_type == "exercise" and question_type:
        exercise_type = metadata.get("题目类型", "")
        if exercise_type:
            if question_type in exercise_type or exercise_type in question_type:
                question_type_match_score = 0.2
            elif question_type == "选择题" and any(option in doc for option in ["A.", "B.", "C.", "D.", "A、", "B、", "C、", "D、"]):
                question_type_match_score = 0.15
            elif question_type == "证明题" and any(keyword in doc for keyword in ["求证", "证明", "证明题", "推导", "推导题"]):
                question_type_match_score = 0.15
            elif question_type == "解答题" and any(keyword in doc for keyword in ["解", "答案", "解析", "求", "计算"]):
                question_type_match_score = 0.15
            elif question_type == "填空题" and any(keyword in doc for keyword in ["__________", "______", "填空", "空"]):
                question_type_match_score = 0.15

    grade_match_score = 0.0
    if grade:
        resource_grade = metadata.get("grade", "") or metadata.get("年级", "")
        if resource_grade:
            if grade in resource_grade or resource_grade in grade:
                grade_match_score = 0.1
            elif grade == "高三" and any(g in resource_grade for g in ["高一", "高二", "高三"]):
                grade_match_score = 0.05
            elif any(target_grade in grade for target_grade in ["高一", "高二", "高三"]) and any(g in resource_grade for g in ["高一", "高二", "高三"]):
                grade_match_score = 0.05

    difficulty_match_score = 0.0
    if difficulty:
        resource_difficulty = metadata.get("difficulty", "") or metadata.get("难度", "") or metadata.get("难度（1-5）", "")
        if resource_difficulty:
            difficulty_map = {
                "基础": ["基础", "简单", "入门", "初级", "1", "2"],
                "中等": ["中等", "一般", "普通", "常见", "2", "3"],
                "拔高": ["拔高", "难", "困难", "挑战", "压轴", "3", "4", "5"],
            }
            for level, keywords in difficulty_map.items():
                if difficulty == level and any(keyword in str(resource_difficulty) for keyword in keywords):
                    difficulty_match_score = 0.1
                    break

    final_relevance = relevance * 0.6 + (
        knowledge_match_score + type_match_score + question_type_match_score + grade_match_score + difficulty_match_score
    ) * 0.4
    final_relevance = max(0.0, min(1.0, final_relevance))

    contains_core_theme = False
    if core_theme:
        title = metadata.get("title", "") or ""
        metadata_str = str(metadata) or ""
        contains_core_theme = core_theme in (doc or "") or core_theme in title or core_theme in metadata_str

    return {
        "current_count": current_count,
        "relevance": final_relevance,
        "contains_core_theme": contains_core_theme,
    }


def matches_exercise_question_type(classified, metadata, doc, query, question_type):
    exercise_type = metadata.get("题目类型", "")
    if not exercise_type:
        print("   ✅ V45.0跳过题目类型过滤: 题目类型为空")
        return True

    if question_type in exercise_type or exercise_type in question_type:
        print(f"   ✅ V45.0题目类型精确匹配: {question_type} 在 {exercise_type} 中")
        return True

    if question_type == "选择题":
        if any(option in doc for option in ["A.", "B.", "C.", "D.", "A、", "B、", "C、", "D、"]):
            print("   ✅ V45.0选择题选项匹配: 发现选项标记")
            return True
        if "选择" in exercise_type:
            print("   ✅ V45.0选择题类型匹配: 题目类型包含'选择'")
            return True
        if any(generic_word in query for generic_word in ["几道", "一些", "给我", "推荐", "有没有", "基础", "简单"]):
            print("   ✅ V45.0通用查询匹配: 查询包含通用词，跳过题目类型过滤")
            return True

    if question_type == "证明题":
        if any(keyword in doc for keyword in ["求证", "证明", "证明题", "推导", "推导题"]):
            print("   ✅ V46.0证明题关键词匹配: 发现证明关键词")
            return True
        if "解答" in exercise_type and any(keyword in doc for keyword in ["证明", "单调性", "求证"]):
            print("   ✅ V46.0证明题匹配: 解答题包含证明内容")
            return True
        if any(keyword in query for keyword in ["单调性", "证明"]) and "解答" in exercise_type:
            print("   ✅ V46.0证明题匹配: 查询包含证明相关词，解答题通过")
            return True
        if "单调性" in query and "解答" in exercise_type:
            knowledge_tags = metadata.get("知识点标签", "")
            if any(keyword in knowledge_tags for keyword in ["单调性", "单调", "增函数", "减函数"]):
                print(f"   ✅ V46.0证明题匹配: 知识点标签'{knowledge_tags}'包含单调性相关关键词")
                return True
        if "解答" in exercise_type:
            print("   ✅ V46.0证明题匹配: 解答题类型，放宽匹配条件")
            return True

    if question_type == "解答题" and any(keyword in doc for keyword in ["解", "答案", "解析", "求", "计算"]):
        print("   ✅ V45.0解答题关键词匹配: 发现解答关键词")
        return True

    if any(generic_word in query for generic_word in ["习题", "题目", "练习题", "测试题", "题"]):
        print("   ✅ V45.0通用查询匹配: 查询包含通用词，跳过题目类型过滤")
        return True

    if question_type == "填空题" and any(keyword in doc for keyword in ["__________", "______", "填空", "空"]):
        print("   ✅ V45.0填空题特征匹配: 发现填空特征")
        return True

    if question_type == "应用题":
        if "应用" in exercise_type:
            print("   ✅ V95.0应用题类型匹配: 题目类型包含'应用'")
            return True
        if any(keyword in doc for keyword in ["实际", "应用", "问题", "情景", "情境", "生活", "生产", "经济", "物理", "化学"]):
            print("   ✅ V95.0应用题内容匹配: 发现应用相关关键词")
            return True
        if any(keyword in (metadata.get("知识点标签", "") or "") for keyword in ["应用", "实际"]):
            print("   ✅ V95.0应用题知识点匹配: 知识点标签包含应用相关词")
            return True
        if "解答" in exercise_type or not exercise_type:
            print("   ✅ V95.0应用题放宽匹配: 解答题或无类型标记")
            return True

    current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
    if current_count < 5:
        print(f"   ✅ V95.0资源不足，放宽题目类型限制: 接受题目类型'{exercise_type}'")
        return True

    print(f"   ⚠️ V45.0跳过不匹配的习题类型: {exercise_type} != {question_type}")
    return False
