from ..._shared import *
from .common import is_specific_theme_query


def evaluate_exercise_match(retriever, doc, metadata, base_relevance, core_theme, query, question_type, multi_theme_info):
    print("   📝 检测到习题资源，使用习题相关性计算方法")
    question_content = metadata.get("题干", "") or doc
    core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    is_consistent = retriever._check_knowledge_point_consistency(metadata, core_theme, question_content, query, base_relevance)
    strict_match = check_exercise_strict_match(retriever, metadata, question_content, core_theme, core_themes)
    specific_theme_query = is_specific_theme_query(core_theme)

    relevance_score = 0.0
    matched_themes = []
    core_theme_match = None
    related_themes = []
    mentioned_themes = []
    is_core_match = False
    match_level = "none"
    explanation = "习题相关性评估"
    should_show = False
    overall_score = 0.0

    if is_consistent:
        relevance_score = base_relevance
        overall_score = base_relevance
        should_show = True
        is_core_match = True
        match_level = "core"
        if not multi_theme_info:
            matched_themes = core_themes
            core_theme_match = core_themes[0] if core_themes else None
        explanation = f"习题知识点与主题一致: {core_theme}"
    elif strict_match:
        relevance_score = base_relevance * 0.5
        overall_score = relevance_score
        should_show = relevance_score > 0.1
        match_level = "related"
        explanation = f"习题知识点与主题部分相关: {core_theme}"
    elif any(st in core_theme for st in ["函数概念", "函数的概念"]):
        print(f"   ⚠️ V30.4严格过滤: '{core_theme}'主题需要严格匹配，知识点不一致，直接过滤")
        explanation = f"严格过滤主题'{core_theme}'知识点不匹配"
    elif base_relevance > 0.5:
        # 高相关性资源，即使知识点不完全匹配也允许通过
        relevance_score = base_relevance * 0.7
        overall_score = relevance_score
        should_show = True
        match_level = "related"
        explanation = f"高相关性资源: {core_theme}"
    elif specific_theme_query:
        # 特定主题查询但知识点不匹配，检查相关性
        if base_relevance > 0.3:
            relevance_score = base_relevance * 0.5
            overall_score = relevance_score
            should_show = True
            match_level = "related"
            explanation = f"主题相关资源: {core_theme}"
        else:
            explanation = f"明确主题查询未命中知识点: {core_theme}"
    else:
        relevance_score = base_relevance * 0.3
        overall_score = relevance_score
        should_show = relevance_score > 0.1
        match_level = "related"
        explanation = f"习题知识点与主题部分相关: {core_theme}"

    relevance_score, overall_score, is_core_match, match_level, explanation, should_show = _boost_proof_questions(
        metadata, question_content, core_theme, query, question_type, relevance_score, overall_score, is_core_match, match_level, explanation, should_show
    )
    relevance_score, overall_score, explanation, should_show, vague_query = _apply_filters(
        retriever, metadata, query, relevance_score, overall_score, explanation, should_show
    )

    return {
        "matched_themes": matched_themes,
        "core_theme_match": core_theme_match,
        "related_themes": related_themes,
        "mentioned_themes": mentioned_themes,
        "is_core_match": is_core_match,
        "match_level": match_level,
        "domain": "习题",
        "explanation": explanation,
        "should_show": should_show,
        "relevance_score": relevance_score,
        "overall_score": overall_score,
        "resource_quality": 0.5,
        "content_completeness": 0.3,
        "teaching_value": 0.15,
        "comprehensiveness": 0.2,
        "concept_hierarchy_factor": 0.5,
    }


def check_exercise_strict_match(retriever, metadata, question_content, core_theme, core_themes):
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "")
    strict_match = True
    
    # 从题目内容提取知识点标签
    if not knowledge_tags and question_content:
        all_math_themes = ["二次函数", "幂函数", "三角函数", "指数函数", "对数函数", "函数的零点", "一次函数", "集合", "不等式", "三角恒等变换"]
        extracted_themes = [t for t in all_math_themes if t in question_content]
        if extracted_themes:
            knowledge_tags = ";".join(extracted_themes)
            print(f"   🔍 V21.0：从题目内容提取知识点标签: '{knowledge_tags}'")
            metadata["知识点"] = knowledge_tags

    if knowledge_tags and core_themes:
        strict_filter_themes = ["函数概念", "函数的概念"]
        is_strict_filter_theme = any(st in core_theme for st in strict_filter_themes)
        generic_themes = ["函数", "数学", "教学", "函数的应用", "高中数学", "数学教学"]
        is_generic_theme = any(gt in core_theme for gt in generic_themes)
        
        if is_strict_filter_theme:
            if metadata.get("resource_type", "") == "ggb" and (not knowledge_tags or knowledge_tags == "unknown"):
                print("   ✅ V61.0GGB资源特殊处理: GGB资源知识点标签为unknown，允许通过筛选")
            else:
                concept_keywords = ["函数概念", "函数的定义", "什么是函数", "函数的意义", "函数表示", "函数表示法", "映射", "对应关系", "自变量", "因变量"]
                if not any(keyword in knowledge_tags for keyword in concept_keywords):
                    print(f"   ⚠️ V30.6严格过滤：知识点标签'{knowledge_tags}'不包含函数概念相关关键词，严格过滤")
                    strict_match = False
        elif not is_generic_theme:
            # 检查是否直接匹配查询主题
            has_query_theme = any(theme in knowledge_tags for theme in core_themes)
            
            if has_query_theme:
                print(f"   ✅ V20.0直接匹配：知识点标签'{knowledge_tags}'包含查询主题{core_themes}")
                strict_match = True
            else:
                # 尝试使用知识图谱扩展匹配
                has_kg_related_match = False
                try:
                    # 获取查询主题的相关概念（包含父概念和子概念）
                    kg = getattr(retriever, 'kg', None)
                    if kg:
                        for theme in core_themes:
                            related_concepts = kg.get_related_nodes(theme)
                            # 检查知识点标签是否包含相关概念
                            for concept in related_concepts:
                                if concept in knowledge_tags:
                                    print(f"   ✅ V20.2知识图谱扩展匹配：知识点标签'{knowledge_tags}'包含相关概念'{concept}'")
                                    has_kg_related_match = True
                                    break
                            if has_kg_related_match:
                                break
                        
                        # 检查知识点标签是否包含相关关键词
                        if not has_kg_related_match:
                            for theme in core_themes:
                                expanded_query = kg.expand_query(theme)
                                expanded_terms = expanded_query.split()
                                for term in expanded_terms:
                                    if term in knowledge_tags:
                                        print(f"   ✅ V20.3知识图谱关键词匹配：知识点标签'{knowledge_tags}'包含扩展关键词'{term}'")
                                        has_kg_related_match = True
                                        break
                                if has_kg_related_match:
                                    break
                except Exception as e:
                    print(f"   ⚠️ 知识图谱匹配失败: {str(e)[:50]}")
                
                if has_kg_related_match:
                    strict_match = True
                else:
                    # 原始严格过滤逻辑：检查是否包含其他不相关的主题
                    all_math_themes = ["二次函数", "幂函数", "三角函数", "指数函数", "对数函数", "函数的零点", "一次函数", "集合", "不等式", "三角恒等变换"]
                    other_themes_in_tags = [t for t in all_math_themes if t in knowledge_tags and t not in core_themes]
                    if other_themes_in_tags:
                        print(f"   ⚠️ V20.1严格过滤：知识点标签'{knowledge_tags}'包含非查询主题{other_themes_in_tags}，但不包含查询主题{core_themes}")
                        strict_match = False
                    else:
                        # 如果没有其他主题，则认为是中性匹配，不过滤
                        print(f"   ✅ V20.4中性匹配：知识点标签'{knowledge_tags}'不包含冲突主题，允许通过")
                        strict_match = True
        else:
            print(f"   ✅ V37.1通用主题处理：查询主题'{core_theme}'是通用主题，允许包含相关知识点标签")
            has_related_keyword = any(keyword in knowledge_tags for keyword in retriever.all_theme_keywords)
            if has_related_keyword:
                print(f"   ✅ V37.1通用主题匹配：知识点标签'{knowledge_tags}'包含相关关键词，通过筛选")
            else:
                core_theme_keywords = retriever.knowledge_hierarchy.get(core_theme, {}).get("keywords", [])
                if any(kw in knowledge_tags for kw in core_theme_keywords):
                    print(f"   ✅ V39.0通用主题匹配：知识点标签'{knowledge_tags}'包含核心主题关键词，通过筛选")
                else:
                    print(f"   ⚠️ V37.1通用主题过滤：知识点标签'{knowledge_tags}'不包含相关关键词，严格过滤")
                    strict_match = False
    return strict_match


def _boost_proof_questions(metadata, question_content, core_theme, query, question_type, relevance_score, overall_score, is_core_match, match_level, explanation, should_show):
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "")
    if (question_type == "证明题" and "单调性" in core_theme) or ("证明" in query and "单调性" in query):
        old_relevance = relevance_score
        relevance_score = max(relevance_score, 0.8)
        overall_score = relevance_score
        print(f"   🔍 V46.1单调性证明题: 提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
        return relevance_score, overall_score, True, "core", f"单调性证明题，提升相关性分数: {core_theme}", True
    if "单调性" in question_content and ("证明" in question_content or "求证" in question_content):
        old_relevance = relevance_score
        relevance_score = max(relevance_score, 0.7)
        overall_score = relevance_score
        print(f"   🔍 V46.2单调性证明题: 基于内容提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
        return relevance_score, overall_score, True, "core", f"单调性证明题，基于内容提升相关性分数: {core_theme}", True
    if "单调性" in knowledge_tags and question_type == "证明题":
        old_relevance = relevance_score
        relevance_score = max(relevance_score, 0.6)
        overall_score = relevance_score
        print(f"   🔍 V46.3单调性证明题: 基于知识点标签提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
        return relevance_score, overall_score, True, "core", f"单调性证明题，基于知识点标签提升相关性分数: {core_theme}", True
    return relevance_score, overall_score, is_core_match, match_level, explanation, should_show


def _apply_filters(retriever, metadata, query, relevance_score, overall_score, explanation, should_show):
    is_vague_query = False
    if should_show and retriever._current_grade_info:
        is_vague_query = retriever._is_vague_grade_query(query, retriever._current_grade_info)
        if is_vague_query:
            print("   🎓 V32.0宽泛查询模式: 放宽年级筛选，广泛推荐")
            grade_filter_result = retriever._apply_flexible_grade_filter(metadata, retriever._current_grade_info)
        else:
            grade_filter_result = retriever._check_grade_match(metadata, retriever._current_grade_info)
        if not grade_filter_result["pass"]:
            print(f"   🎓 V32.0年级筛选: {grade_filter_result['reason']}")
            return 0.0, 0.0, f"{explanation} (年级不符: {grade_filter_result['reason']})", False, is_vague_query

    if should_show and retriever._current_subjective_intent:
        intent_filter_result = retriever._apply_subjective_intent_filter(metadata, retriever._current_subjective_intent, is_vague_query)
        if not intent_filter_result["pass"]:
            print(f"   💭 V32.0主观意图筛选: {intent_filter_result['reason']}")
            return 0.0, 0.0, f"{explanation} (主观意图不符: {intent_filter_result['reason']})", False, is_vague_query
        if intent_filter_result.get("score_adjustment"):
            old_relevance = relevance_score
            relevance_score *= intent_filter_result["score_adjustment"]
            overall_score *= intent_filter_result["score_adjustment"]
            print(f"   💭 V32.0主观意图调整: 相关性 {old_relevance:.3f} -> {relevance_score:.3f} (乘以 {intent_filter_result['score_adjustment']})")

    return relevance_score, overall_score, explanation, should_show, is_vague_query
