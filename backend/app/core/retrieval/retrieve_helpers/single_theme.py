from .._shared import *
import re
import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from .filters import (
    adjust_single_theme_result_count,
    build_resource_type_filters,
    has_specific_resource_types,
)
from app.core.retrieval.methods.expand_theme import ThemeExpander, expand_themes_for_retrieval
from .semantic_matcher import semantic_matcher

logger = logging.getLogger(__name__)

SEMANTIC_RESOURCE_TYPES = {
    "教案",
    "教学设计",
    "教学方案",
    "教学计划",
    "备课",
    "导学案",
    "详案",
    "简案",
    "教学反思",
    "核心素养",
    "课件",
    "PPT",
    "幻灯片",
    "演示文稿",
    "课件资源",
    "教学大纲",
    "大纲",
    "课程标准",
}
EXERCISE_RESOURCE_TYPES = {"习题", "题目", "练习题", "选择题", "填空题", "解答题", "证明题"}

# 板块路径映射
BOARD_PATH_MAPPING = {
    "函数": "01-函数",
    "几何": "02-几何",
    "概率统计": "03-概率与统计",
    "代数": "代数",
}

# 不需要板块过滤的资源类型
RESOURCE_TYPES_NO_BOARD_FILTER = {"theory", "优秀教案共性", "excellent_case"}

# 从核心主题获取顶级板块
def _get_top_board(core_theme, knowledge_hierarchy):
    if not core_theme:
        return None
    theme_info = knowledge_hierarchy.get(core_theme, {})
    parent_topic = theme_info.get("parent_topic")

    if not parent_topic:
        # 直接检查核心主题是否包含板块相关关键词
        # 优先级：复数/代数 > 函数 > 几何 > 概率统计
        if "概率" in core_theme:
            return "概率统计"
        elif "函数" in core_theme:
            return "函数"
        elif "代数" in core_theme or "复数" in core_theme or "虚数" in core_theme:
            return "代数"
        elif "几何" in core_theme or "平面" in core_theme or "空间" in core_theme:
            return "几何"
        # 检查板块名称是否在核心主题中
        for board_name in BOARD_PATH_MAPPING.keys():
            if board_name in core_theme:
                return board_name
        return None

    if parent_topic in BOARD_PATH_MAPPING.keys():
        return parent_topic
    # 检查父主题是否包含板块相关关键词
    # 优先级：复数/代数 > 函数 > 几何 > 概率统计
    if "概率" in parent_topic:
        return "概率统计"
    elif "函数" in parent_topic:
        return "函数"
    elif "代数" in parent_topic or "复数" in parent_topic:
        return "代数"
    elif "几何" in parent_topic:
        return "几何"
    # 检查板块名称是否在父主题中
    for board_name in BOARD_PATH_MAPPING.keys():
        if board_name in parent_topic or parent_topic in board_name:
            return board_name
    return None

# 从资源路径获取板块
def _get_resource_board(source_file, resource_type):
    if resource_type in RESOURCE_TYPES_NO_BOARD_FILTER:
        return None
    if not source_file:
        return None
    # 特殊处理代数相关的资源（优先级最高）
    if "代数" in source_file or "复数" in source_file or "虚数" in source_file:
        return "代数"
    # 然后检查路径前缀匹配
    for board_name, path_prefix in BOARD_PATH_MAPPING.items():
        if path_prefix in source_file:
            return board_name
    return None


def _should_preserve_query_text(resource_types):
    return bool(resource_types) and any(rt in SEMANTIC_RESOURCE_TYPES for rt in resource_types)


def _is_general_material_query(query, resource_types):
    generic_words = ["资料", "学习资料", "教学资源", "资源", "内容"]
    return (not resource_types or any(rt in {"资料", "资源", "教学资源", "学习资料"} for rt in resource_types)) and any(
        word in (query or "") for word in generic_words
    )


def _should_apply_semantic_supplement(query, resource_types, core_theme):
    # 如果指定了具体的资源类型，不应用语义补充
    if resource_types:
        return False
    return bool(core_theme) and (
        _should_preserve_query_text(resource_types)
        or _is_general_material_query(query, resource_types)
        or bool(resource_types) and any(rt in EXERCISE_RESOURCE_TYPES for rt in resource_types)
    )


def _text_match_score(core_theme, metadata, document):
    normalized_theme = _normalize_match_text(core_theme)
    title = metadata.get("title", "") or ""
    source_file = metadata.get("source_file", "") or ""
    knowledge_tags = metadata.get("知识点标签", "") or metadata.get("知识点", "") or ""
    text = _normalize_match_text(f"{title} {source_file} {knowledge_tags} {document or ''}")

    if not normalized_theme:
        return 0.0

    # 特殊处理分层抽样和分层随机抽样的匹配
    if normalized_theme == "分层抽样":
        if "分层抽样" in _normalize_match_text(title) or "分层随机抽样" in _normalize_match_text(title):
            return 1.0
        if "分层抽样" in _normalize_match_text(source_file) or "分层随机抽样" in _normalize_match_text(source_file):
            return 0.9
        if "分层抽样" in _normalize_match_text(knowledge_tags) or "分层随机抽样" in _normalize_match_text(knowledge_tags):
            return 0.85
        if "分层抽样" in text or "分层随机抽样" in text:
            return 0.7
        return 0.0

    if normalized_theme in _normalize_match_text(title):
        return 1.0
    if normalized_theme in _normalize_match_text(source_file):
        return 0.9
    if normalized_theme in _normalize_match_text(knowledge_tags):
        return 0.85
    if normalized_theme in text:
        return 0.7
    return 0.0


def _normalize_match_text(text):
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("的", "")
    normalized = re.sub(r"[\s,，。；;、:：()\[\]（）\-_/]+", "", normalized)
    return normalized


def _build_semantic_supplement(collection, where_filter, core_theme, limit):
    try:
        if where_filter:
            raw = collection.get(where=where_filter, include=["documents", "metadatas"])
        else:
            raw = collection.get(include=["documents", "metadatas"])
    except Exception as exc:
        print(f"   ⚠️ 语义补召回失败: {exc}")
        return None

    documents = raw.get("documents") or []
    metadatas = raw.get("metadatas") or []
    ids = raw.get("ids") or []
    scored = []

    for index, metadata in enumerate(metadatas):
        document = documents[index] if index < len(documents) else ""
        score = _text_match_score(core_theme, metadata or {}, document or "")
        if score <= 0:
            continue
        scored.append((score, document, metadata or {}, ids[index] if index < len(ids) else f"supplement_{index}"))

    if not scored:
        return None

    scored.sort(key=lambda item: -item[0])
    top_items = scored[:limit]
    print(f"   🔎 语义补召回命中 {len(top_items)} 条，主题='{core_theme}'")

    return {
        "documents": [[item[1] for item in top_items]],
        "metadatas": [[item[2] for item in top_items]],
        "distances": [[max(0.05, 0.6 - item[0] * 0.4) for item in top_items]],
        "ids": [[f"semantic_{item[3]}" for item in top_items]],
    }


def _merge_query_results(primary_results, supplement_results):
    """
    合并两个检索结果，优先保留primary_results（精确匹配结果）
    """
    if not primary_results:
        return supplement_results
    if not supplement_results:
        return primary_results

    # 优先保留primary_results（精确匹配结果），将supplement_results（向量检索）排在后面
    merged = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    for key in ("documents", "metadatas", "distances", "ids"):
        # 先添加primary_results（精确匹配），再添加supplement_results（向量检索）
        merged[key][0].extend(primary_results.get(key, [[]])[0] if primary_results.get(key) else [])
        merged[key][0].extend(supplement_results.get(key, [[]])[0] if supplement_results.get(key) else [])
    return merged


def execute_single_theme_retrieval(
    retriever,
    collection,
    query,
    core_theme,
    n_results,
    resource_types,
    question_type,
    exclude_keywords=None,
    requirements=None,
):
    logger.info("V100.0调试 - execute_single_theme_retrieval开始")
    logger.info(f"V100.0调试 - query: '{query}'")
    logger.info(f"V100.0调试 - core_theme: '{core_theme}'")
    logger.info(f"V100.0调试 - resource_types: {resource_types}")
    logger.info(f"V100.0调试 - has_specific_resource_types: {has_specific_resource_types(resource_types)}")
    
    if not core_theme and not has_specific_resource_types(resource_types):
        logger.warning("未识别到核心主题，停止检索并返回空结果")
        return query, core_theme, None

    if has_specific_resource_types(resource_types):
        query_to_use = query
        logger.info(f"V83.0执行资源类型查询，使用原始查询作为查询文本: '{query_to_use}'")
    else:
        query_to_use = core_theme
        logger.info(f"执行单主题检索，查询: '{query_to_use}'")

    resource_type_filters, where_filter = build_resource_type_filters(query, resource_types, question_type)
    detected_intents = retriever._detect_query_intents(query)

    # 主题词扩展 - 将短的主题词扩展为更具体的同义词和关联词
    expanded_themes = []
    if core_theme:
        # 处理多个主题的情况
        themes = core_theme.split(',') if isinstance(core_theme, str) else core_theme
        themes = [theme.strip() for theme in themes if theme.strip()]
        
        # 使用主题词扩展器扩展主题
        expander = ThemeExpander(knowledge_hierarchy=retriever.knowledge_hierarchy if hasattr(retriever, 'knowledge_hierarchy') else None)
        expanded_themes = expander.expand_multiple(themes)
        if len(expanded_themes) > 1:
            print(f"\n🔍 V101.0 主题词扩展: '{core_theme}' -> {expanded_themes}")

    if core_theme:
        if _should_preserve_query_text(resource_types):
            # 修复：保留用户查询中的关键条件（如"练习课"），避免信息丢失
            # 使用核心主题 + 原始查询中的关键条件进行检索
            if core_theme and resource_types:
                # 从原始查询中提取关键条件（如"练习课"、"复习课"等）
                key_conditions = []
                for keyword in ['练习课', '复习课', '习题课', '新授课', '综合训练']:
                    if keyword in query_to_use:
                        key_conditions.append(keyword)
                
                if key_conditions:
                    enhanced_query = f"{core_theme} {' '.join(key_conditions)}"
                    print(f"   V201.0修复: 使用核心主题+关键条件组合: '{enhanced_query}'")
                else:
                    enhanced_query = core_theme
                    print(f"   V200.0使用核心主题+资源类型组合: '{enhanced_query}'")
            else:
                enhanced_query = query_to_use
                print(f"   V51.1保留资源类型语义作为查询文本: '{enhanced_query}'")
        else:
            enhanced_query = core_theme
            print(f"   V51.2使用核心主题作为查询文本: '{enhanced_query}'")
    else:
        enhanced_query = retriever._enhance_query_dynamically(query_to_use, detected_intents)
        print(f"   🔍 V51.0动态查询增强: '{query_to_use}' -> '{enhanced_query}'")

    # 添加精确匹配步骤
    exact_match_results = None
    print(f"🔍 V100.0调试 - core_theme: '{core_theme}', resource_types: {resource_types}")
    print(f"🔍 V100.0调试 - has_specific_resource_types: {has_specific_resource_types(resource_types)}")
    print(f"🔍 V100.0调试 - core_theme is not None: {core_theme is not None}")
    print(f"🔍 V100.0调试 - bool(core_theme): {bool(core_theme)}")
    
    # V41.6修复：对于GGB资源，强制使用精确匹配（关键词匹配），确保教学用途字段被正确匹配
    is_ggb_query = any(rt and 'ggb' in rt.lower() for rt in (resource_types or []))
    print(f"🔍 V41.6调试 - is_ggb_query: {is_ggb_query}")
    
    # 条件修改：GGB资源或者有特定资源类型时都执行精确匹配
    if core_theme and (has_specific_resource_types(resource_types) or is_ggb_query):
        print(f"\n🔍 V100.0执行精确匹配，核心主题: '{core_theme}'")
        try:
            exact_match_where = where_filter.copy() if where_filter else {}
            print(f"🔍 V100.0调试 - exact_match_where: {exact_match_where}")
            exact_match_results = collection.get(
                where=exact_match_where,
                include=["documents", "metadatas"]
            )
            
            if exact_match_results and exact_match_results.get("documents"):
                print(f"🔍 V100.0调试 - collection.get返回 {len(exact_match_results['documents'])} 条结果")
                # 过滤包含核心主题或其关键词的结果
                filtered_docs = []
                filtered_metas = []
                filtered_ids = []
                
                # 提取核心主题的关键词
                core_theme_keywords = []
                # 处理多个主题的情况
                themes = core_theme.split(',') if isinstance(core_theme, str) else core_theme
                themes = [theme.strip() for theme in themes if theme.strip()]
                
                # 对于每个主题，提取关键词
                import jieba
                for theme in themes:
                    theme_keywords = list(jieba.cut(theme))
                    theme_keywords = [kw for kw in theme_keywords if len(kw) > 1]  # 过滤单字
                    core_theme_keywords.extend(theme_keywords)
                
                # 去重
                core_theme_keywords = list(set(core_theme_keywords))
                print(f"🔍 V100.0调试 - 核心主题关键词: {core_theme_keywords}")
                
                for doc, meta, id_ in zip(exact_match_results["documents"], exact_match_results["metadatas"], exact_match_results["ids"]):
                    title = meta.get("title", "")
                    source_file = meta.get("source_file", "")
                    knowledge_tags = meta.get("知识点", "") or meta.get("知识点标签", "")
                    teaching_use = meta.get("教学用途", "") or ""  # V41.5新增：加入教学用途字段
                    
                    haystack = f"{title} {source_file} {knowledge_tags} {teaching_use}"  # V41.5新增：加入教学用途
                    
                    # 检查核心主题或其关键词是否在文档中出现
                    match_found = False
                    
                    # 处理多个主题的情况
                    themes = core_theme.split(',') if isinstance(core_theme, str) else core_theme
                    themes = [theme.strip() for theme in themes if theme.strip()]
                    
                    # 检查是否包含任何一个主题
                    for theme in themes:
                        if theme in haystack:
                            match_found = True
                            break
                    
                    # 特殊处理分层抽样
                    if not match_found and "分层抽样" in themes and "分层随机抽样" in haystack:
                        match_found = True
                    
                    # 检查核心主题的关键词
                    if not match_found:
                        for keyword in core_theme_keywords:
                            if keyword in haystack:
                                match_found = True
                                break
                    
                    if match_found:
                        filtered_docs.append(doc)
                        filtered_metas.append(meta)
                        filtered_ids.append(id_)
                        print(f"   ✅ 精确匹配: '{meta.get('title', '未知')}'")
                
                if filtered_docs:
                    print(f"   ✅ 精确匹配找到 {len(filtered_docs)} 条结果")
                    exact_match_results = {
                        "documents": [filtered_docs],
                        "metadatas": [filtered_metas],
                        "ids": [filtered_ids],
                        "distances": [[0.0] * len(filtered_docs)]
                    }
                else:
                    print(f"   ⚠️ 精确匹配未找到结果，继续向量检索")
                    exact_match_results = None
            else:
                print(f"   ⚠️ 精确匹配未找到结果，继续向量检索")
                exact_match_results = None
        except Exception as e:
            print(f"   ⚠️ 精确匹配失败: {e}，继续向量检索")
            exact_match_results = None

    n_results_per_query = n_results or retriever.DEFAULT_N_RESULTS
    n_results_adjusted = adjust_single_theme_result_count(
        retriever,
        query,
        query_to_use,
        detected_intents,
        n_results_per_query,
        core_theme,
        question_type,
        resource_types,
    )

    if resource_type_filters:
        logger.info(f"V54.1组合资源查询: 为 {len(resource_type_filters)} 种资源类型单独检索")
        all_results = []
        
        # V100.1新增：对于课件资源，优先执行精确匹配
        courseware_filter = next((rf for rf in resource_type_filters if rf.get("resource_type") == "courseware"), None)
        
        for resource_filter in resource_type_filters:
            resource_type = resource_filter["resource_type"]
            logger.info(f"为资源类型 '{resource_type}' 执行检索...")
            
            # V100.1新增：课件资源优先执行精确匹配
            if resource_type == "courseware" and core_theme:
                logger.info("V100.1课件资源优先执行精确匹配")
                try:
                    exact_match_results_courseware = collection.get(
                        where=resource_filter,
                        include=["documents", "metadatas"]
                    )
                    
                    if exact_match_results_courseware and exact_match_results_courseware.get("documents"):
                        logger.info(f"V100.1调试 - ChromaDB返回的原始课件数量: {len(exact_match_results_courseware['documents'])}")
                        logger.info(f"V100.1调试 - 检查第一条课件的metadata: {exact_match_results_courseware['metadatas'][0] if exact_match_results_courseware['metadatas'] else 'None'}")
                        # 过滤包含核心主题或其关键词的结果
                        filtered_docs = []
                        filtered_metas = []
                        filtered_ids = []
                        
                        # 提取核心主题的关键词
                        core_theme_keywords = []
                        themes = core_theme.split(',') if isinstance(core_theme, str) else core_theme
                        themes = [theme.strip() for theme in themes if theme.strip()]
                        
                        import jieba
                        for theme in themes:
                            theme_keywords = list(jieba.cut(theme))
                            theme_keywords = [kw for kw in theme_keywords if len(kw) > 1]
                            core_theme_keywords.extend(theme_keywords)
                        core_theme_keywords = list(set(core_theme_keywords))
                        
                        for doc, meta, id_ in zip(exact_match_results_courseware["documents"],
                                                  exact_match_results_courseware["metadatas"],
                                                  exact_match_results_courseware["ids"]):
                            title = meta.get("title", "") or ""
                            teaching_use = meta.get("教学用途", "") or ""
                            haystack = f"{title} {teaching_use}"
                            logger.info(f"V100.1调试 - 资源ID: {id_}, title: {title}, teaching_use: {teaching_use}")
                            logger.info(f"V100.1调试 - haystack: {haystack}")

                            match_found = False
                            for theme in themes:
                                if theme in haystack:
                                    match_found = True
                                    break
                            if not match_found:
                                for keyword in core_theme_keywords:
                                    if keyword in haystack:
                                        match_found = True
                                        break
                            
                            if match_found:
                                filtered_docs.append(doc)
                                filtered_metas.append(meta)
                                filtered_ids.append(id_)
                        
                        if filtered_docs:
                            logger.info(f"课件精确匹配找到 {len(filtered_docs)} 条结果")
                            logger.info(f"V100.1调试 - 课件资源IDs: {filtered_ids[:5]}...")
                            theme_results = {
                                "documents": [filtered_docs],
                                "metadatas": [filtered_metas],
                                "ids": [filtered_ids],
                                "distances": [[0.0] * len(filtered_docs)]
                            }
                            all_results.append((resource_type, theme_results))
                            continue  # 跳过向量检索，直接使用精确匹配结果
                        else:
                            logger.warning("课件精确匹配未找到结果，继续向量检索")
                            logger.warning(f"V100.1调试 - 原始课件数量: {len(exact_match_results_courseware['documents'])}, 过滤后: 0")
                except Exception as e:
                    logger.warning(f"课件精确匹配失败: {e}，继续向量检索")

            # 使用扩展后的主题进行多查询检索
            theme_results = None
            try:
                if len(expanded_themes) > 1:
                    logger.info(f"V101.0 使用扩展主题多查询检索: {expanded_themes}")
                    theme_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

                    # 为每个扩展主题执行查询
                    for exp_theme in expanded_themes:
                        logger.info(f"查询扩展主题: '{exp_theme}'")
                        exp_results = collection.query(
                            query_texts=[exp_theme],
                            n_results=n_results_adjusted,
                            where=resource_filter,
                            include=["documents", "metadatas", "distances"],
                        )
                        if exp_results and exp_results.get("documents") and exp_results["documents"][0]:
                            theme_results["documents"][0].extend(exp_results["documents"][0])
                            theme_results["metadatas"][0].extend(exp_results["metadatas"][0])
                            theme_results["distances"][0].extend([d * 0.9 for d in exp_results["distances"][0]])  # 稍微降低扩展主题的权重
                            theme_results["ids"][0].extend([f"{resource_type}_{exp_theme}_{i}" for i in range(len(exp_results["documents"][0]))])
                            logger.info(f"扩展主题 '{exp_theme}' 找到 {len(exp_results['documents'][0])} 条结果")

                    # 如果没有找到任何结果，使用原始查询
                    if not theme_results["documents"][0]:
                        logger.warning("所有扩展主题均未找到结果，使用原始查询")
                        theme_results = collection.query(
                            query_texts=[enhanced_query],
                            n_results=n_results_adjusted,
                            where=resource_filter,
                            include=["documents", "metadatas", "distances"],
                        )
                        theme_results["ids"] = [[f"{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
                else:
                    # 单主题查询（原有逻辑）
                    theme_results = collection.query(
                        query_texts=[enhanced_query],
                        n_results=n_results_adjusted,
                        where=resource_filter,
                        include=["documents", "metadatas", "distances"],
                    )
                    theme_results["ids"] = [[f"{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
            except Exception as e:
                logger.warning(f"向量检索失败: {e}")
                theme_results = None

            if theme_results and theme_results.get("documents") and theme_results["documents"][0]:
                logger.info(f"找到 {len(theme_results['documents'][0])} 条结果")
                all_results.append((resource_type, theme_results))
            else:
                logger.warning("未找到结果")

        if all_results:
            logger.info(f"合并 {len(all_results)} 种资源类型的检索结果...")
            logger.info(f"V100.1调试 - all_results内容: {[(rt, len(tr['documents'][0])) for rt, tr in all_results]}")
            results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
            for resource_type, theme_results in all_results:
                results["documents"][0].extend(theme_results["documents"][0])
                results["metadatas"][0].extend(theme_results["metadatas"][0])
                results["distances"][0].extend(theme_results["distances"][0])
                results["ids"][0].extend(theme_results["ids"][0])
            logger.info(f"合并完成，共 {len(results['documents'][0])} 条结果")
        else:
            logger.warning("所有资源类型均未找到结果，尝试使用精确匹配结果")
            # 如果向量检索失败，使用精确匹配的结果
            results = exact_match_results
    else:
        logger.info("V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索")

        # 使用扩展后的主题进行多查询检索
        if len(expanded_themes) > 1:
            logger.info(f"V101.0 使用扩展主题多查询检索: {expanded_themes}")
            results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

            # 为每个扩展主题执行查询
            for exp_theme in expanded_themes:
                logger.info(f"查询扩展主题: '{exp_theme}'")
                try:
                    exp_results = collection.query(
                        query_texts=[exp_theme],
                        n_results=n_results_adjusted,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"],
                    )
                    if exp_results and exp_results.get("documents") and exp_results["documents"][0]:
                        results["documents"][0].extend(exp_results["documents"][0])
                        results["metadatas"][0].extend(exp_results["metadatas"][0])
                        results["distances"][0].extend([d * 0.9 for d in exp_results["distances"][0]])  # 稍微降低扩展主题的权重
                        results["ids"][0].extend([f"query_{exp_theme}_{i}" for i in range(len(exp_results["documents"][0]))])
                        logger.info(f"扩展主题 '{exp_theme}' 找到 {len(exp_results['documents'][0])} 条结果")
                except Exception as e:
                    logger.warning(f"扩展主题查询失败: {e}")

            # 如果没有找到任何结果，使用原始查询
            if not results["documents"][0]:
                logger.warning("所有扩展主题均未找到结果，使用原始查询")
                try:
                    results = collection.query(
                        query_texts=[enhanced_query],
                        n_results=n_results_adjusted,
                        where=where_filter,
                        include=["documents", "metadatas", "distances"],
                    )
                    results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]
                except Exception as e:
                    logger.warning(f"原始查询失败: {e}")
        else:
            # 单主题查询（原有逻辑）
            try:
                results = collection.query(
                    query_texts=[enhanced_query],
                    n_results=n_results_adjusted,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"],
                )
                results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]
            except Exception as e:
                logger.warning(f"单主题查询失败: {e}")
                results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
            
        # 如果向量检索失败，使用精确匹配的结果
        if not results or not results.get("documents") or not results["documents"][0]:
            logger.warning("向量检索未找到结果，尝试使用精确匹配结果")
            results = exact_match_results

    supplement_where = where_filter
    if _is_general_material_query(query, resource_types):
        supplement_where = None

    # 合并精确匹配结果
    if exact_match_results and results:
        logger.info("合并精确匹配结果...")
        results = _merge_query_results(exact_match_results, results)
        logger.info(f"合并完成，共 {len(results['documents'][0])} 条结果")

    if _should_apply_semantic_supplement(query, resource_types, core_theme):
        supplement_results = _build_semantic_supplement(
            collection,
            supplement_where,
            core_theme,
            limit=min(40, max(10, n_results_adjusted // 4)),
        )
        results = _merge_query_results(results, supplement_results)

    logger.info(f"V100.0调试 - execute_single_theme_retrieval返回结果数量: {len(results.get('documents', [[]])[0]) if results and results.get('documents') else 'None'}")
    logger.info(f"V100.1调试 - 返回结果中的资源类型分布:")
    if results and results.get('metadatas'):
        type_count = {}
        for meta in results['metadatas'][0]:
            rt = meta.get('resource_type', 'unknown')
            type_count[rt] = type_count.get(rt, 0) + 1
        for rt, count in type_count.items():
            logger.info(f"  {rt}: {count}")
    return query_to_use, core_theme, results


def postprocess_single_theme_results(retriever, query, results, resource_types, core_theme, exclude_keywords=None, requirements=None):
    logger.info(f"postprocess_single_theme_results 被调用")
    logger.info(f"   查询: '{query}'")
    logger.info(f"   核心主题: '{core_theme}'")
    logger.info(f"   资源类型: {resource_types}")
    logger.info(f"   排除关键词: {exclude_keywords}")
    logger.info(f"   用户要求: {requirements}")
    logger.info(f"   原始结果数量: {len(results.get('documents', [[]])[0]) if results and results.get('documents') else 'None'}")

    if not (results and results.get("documents") and results["documents"][0]):
        logger.warning("结果为空，直接返回None")
        return None

    if not results.get("ids") or not results["ids"][0]:
        results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]

    if results.get("metadatas") and results["metadatas"][0]:
        unique_results = retriever._deduplicate_results(results)
        print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
        results = unique_results

    # 获取查询的顶级板块
    top_board = _get_top_board(core_theme, retriever.knowledge_hierarchy)
    if top_board:
        print(f"   🎯 板块过滤开启 - 查询板块: '{top_board}', 核心主题: '{core_theme}'")
    else:
        print(f"   ⚠️ 未识别到查询板块，核心主题: '{core_theme}'")

    filtered_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    
    # 检查结果结构
    logger.info(f"结果结构检查:")
    logger.info(f"  - documents[0] 长度: {len(results['documents'][0]) if results.get('documents') and results['documents'] else 'None'}")
    logger.info(f"  - metadatas[0] 长度: {len(results['metadatas'][0]) if results.get('metadatas') and results['metadatas'] else 'None'}")
    logger.info(f"  - distances[0] 长度: {len(results['distances'][0]) if results.get('distances') and results['distances'] else 'None'}")
    logger.info(f"  - ids[0] 长度: {len(results['ids'][0]) if results.get('ids') and results['ids'] else 'None'}")
    
    # 检查 distances 和 ids 的实际内容
    if results.get('distances') and results['distances']:
        logger.info(f"  - distances 类型: {type(results['distances'])}")
        logger.info(f"  - distances[0] 类型: {type(results['distances'][0])}")
        if results['distances'][0]:
            logger.info(f"  - distances[0][0]: {results['distances'][0][0]}")
    
    if results.get('ids') and results['ids']:
        logger.info(f"  - ids 类型: {type(results['ids'])}")
        logger.info(f"  - ids[0] 类型: {type(results['ids'][0])}")
        if results['ids'][0]:
            logger.info(f"  - ids[0][0]: {results['ids'][0][0]}")
    
    logger.info(f"开始遍历结果进行过滤...")
    processed_count = 0

    try:
        for doc, meta, dist, id_ in zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0]):
            processed_count += 1
            if processed_count <= 5:
                dist_str = f"{dist:.3f}" if dist is not None else "None"
                logger.info(f"处理第 {processed_count} 条结果: title='{meta.get('title', '未知')}', dist={dist_str}")
            
            # 排除关键词过滤 - 如果标题或内容中包含排除关键词，则跳过
            if exclude_keywords:
                title = meta.get('title', '') or ''
                content_snippet = doc[:500] if doc else ''  # 只取前500字符进行匹配
                excluded = False
                for exclude_kw in exclude_keywords:
                    if exclude_kw in title:
                        print(f"   ⚠️ 过滤（排除关键词）：标题包含'{exclude_kw}': '{title}'")
                        excluded = True
                        break
                    elif exclude_kw in content_snippet:
                        print(f"   ⚠️ 过滤（排除关键词）：内容包含'{exclude_kw}': '{title}'")
                        excluded = True
                        break
                if excluded:
                    continue  # 跳过包含排除关键词的文档

            kg = getattr(retriever, 'kg', None)
            if not _passes_unified_semantic_gate(query, core_theme, doc, meta, dist, kg):
                print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 语义门控未通过 (距离: {dist:.3f})")
                continue

            # 板块过滤（作为分板块检索的双重保险）- 临时禁用以调试
            resource_type = meta.get("resource_type", "")
            # logger.info(f"资源类型: '{resource_type}', 标题: '{meta.get('title', '未知')}'")
            
            # 直接保留结果，跳过板块过滤
            filtered_results["documents"][0].append(doc)
            filtered_results["metadatas"][0].append(meta)
            filtered_results["distances"][0].append(dist)
            filtered_results["ids"][0].append(id_)
            # logger.info(f"保留：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
    except Exception as e:
        logger.error(f"遍历结果时发生异常: {e}")
        import traceback
        logger.error(traceback.format_exc())

    logger.info(f"过滤后结果数量: {len(filtered_results['documents'][0])}")

    if filtered_results["documents"][0]:
        print(f"   ✅ 单主题查询过滤完成，保留 {len(filtered_results['documents'][0])} 条结果")
        
        # 使用语义匹配排序结果
        if requirements:
            print(f"   🔍 使用语义匹配排序结果，要求: {requirements}")
            filtered_results = _sort_results_by_semantic_score(filtered_results, requirements)
            print(f"   ✅ 语义排序完成")
        
        return filtered_results

    logger.warning("单主题查询过滤后无结果")
    return None


def _passes_unified_semantic_gate(query, core_theme, doc, meta, distance, kg=None):
    if distance is None:
        logger.warning(f"语义门控未通过: distance is None")
        return False
    
    title = meta.get('title', '') or ''
    source_file = meta.get('source_file', '') or ''
    knowledge_tags = meta.get('知识点', '') or meta.get('知识点标签', '') or ''
    resource_type = meta.get('resource_type', '') or ''
    teaching_use = meta.get('教学用途', '') or ''  # V41.3新增：包含教学用途字段
    text = _normalize_match_text(
        f"{doc} {title} {knowledge_tags} {source_file} {teaching_use}"  # V41.3新增：加入教学用途
    )
    
    # 对GGB资源放宽语义门控要求
    is_ggb_resource = resource_type.lower() == 'ggb' or 'ggb' in source_file.lower()
    
    if core_theme:
        theme_keywords = _extract_theme_keywords(core_theme)
        has_direct_match = any(_normalize_match_text(kw) in text for kw in theme_keywords)
        
        incompatible_topics = _get_incompatible_topics(core_theme, kg)
        has_incompatible = any(_normalize_match_text(topic) in text for topic in incompatible_topics)
        
        # V41.5改进：课件资源通常包含多个相关主题，不应该因为包含“兄弟概念”而被过滤
        # 例如：“棱柱、棱锥和棱台”是一个综合性课件，应该被保留
        is_courseware_resource = resource_type.lower() == 'courseware' or '课件' in teaching_use
        if has_incompatible and not is_courseware_resource:
            logger.info(f"语义门控未通过(存在不兼容主题): distance={distance:.3f}, 核心主题='{core_theme}', 不兼容主题={incompatible_topics}")
            return False
        elif has_incompatible and is_courseware_resource:
            logger.info(f"语义门控通过(课件资源包含相关主题): distance={distance:.3f}, 核心主题='{core_theme}', 包含主题={incompatible_topics}")
            # 课件资源即使包含不兼容主题也继续检查其他条件
        
        if distance <= 0.80:
            if has_direct_match:
                logger.info(f"语义门控通过(高置信度+直接匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
            elif distance <= 0.65:
                logger.info(f"语义门控通过(极高置信度): distance={distance:.3f}")
                return True
        
        if distance <= 0.90:
            if has_direct_match:
                logger.info(f"语义门控通过(中置信度+直接匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
        
        if has_direct_match:
            if distance <= 0.95:
                logger.info(f"语义门控通过(直接主题匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
        
        if distance <= 0.85:
            logger.info(f"语义门控通过(较低距离): distance={distance:.3f}")
            return True
        
        # GGB资源额外放宽：距离<=1.2且标题、文件名或教学用途包含核心主题关键词
        if is_ggb_resource and distance <= 1.2:
            title_normalized = _normalize_match_text(title)
            source_file_normalized = _normalize_match_text(source_file)
            teaching_use_normalized = _normalize_match_text(teaching_use)  # V41.3新增：加入教学用途字段
            for kw in theme_keywords:
                kw_normalized = _normalize_match_text(kw)
                # V41.3修改：增加对教学用途字段的检查
                if kw_normalized in title_normalized or kw_normalized in source_file_normalized or kw_normalized in teaching_use_normalized:
                    logger.info(f"语义门控通过(GGB资源放宽+关键词匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                    return True
            # GGB资源如果标题、文件名或教学用途包含"坐标"且距离<=1.5也通过
            # V41.3修改：增加对教学用途字段的检查
            if distance <= 1.5 and ("坐标" in title_normalized or "坐标" in source_file_normalized or "坐标" in teaching_use_normalized):
                logger.info(f"语义门控通过(GGB资源放宽+坐标关键词): distance={distance:.3f}, 核心主题='{core_theme}'")
                return True
        
        # V41.4新增：课件资源额外放宽
        # 课件资源的向量相似度通常较低（因为只有标题和教学用途字段），需要放宽阈值
        # V100.1修改：将课件资源阈值从1.0调整到1.1，提高课件资源的召回率
        is_courseware_resource = resource_type.lower() == 'courseware' or '课件' in teaching_use
        if is_courseware_resource and distance <= 1.1:
            title_normalized = _normalize_match_text(title)
            source_file_normalized = _normalize_match_text(source_file)
            teaching_use_normalized = _normalize_match_text(teaching_use)
            for kw in theme_keywords:
                kw_normalized = _normalize_match_text(kw)
                if kw_normalized in title_normalized or kw_normalized in source_file_normalized or kw_normalized in teaching_use_normalized:
                    logger.info(f"语义门控通过(课件资源放宽+关键词匹配): distance={distance:.3f}, 核心主题='{core_theme}'")
                    return True
        
        logger.info(f"语义门控未通过: distance={distance:.3f}, 核心主题='{core_theme}', 文本中未找到匹配")
        return False
    else:
        result = distance <= 1.10
        logger.info(f"语义门控(无核心主题): distance={distance:.3f}, result={result}")
        return result


def _get_incompatible_topics(core_theme, kg=None):
    if kg:
        siblings = kg.get_sibling_concepts(core_theme)
        if siblings:
            return siblings
    
    fallback_incompatible = []
    function_types = ['指数函数', '幂函数', '对数函数', '三角函数', '反函数']
    
    for func_type in function_types:
        if func_type in core_theme:
            fallback_incompatible = [f for f in function_types if f != func_type]
            fallback_incompatible.extend(['函数的表示法', '映射'])
            break
    
    if '立体几何' in core_theme or '空间向量' in core_theme:
        fallback_incompatible = ['平面几何', '解析几何']
    elif '概率' in core_theme or '统计' in core_theme:
        fallback_incompatible = ['函数', '几何', '代数']
    
    return fallback_incompatible


def _extract_theme_keywords(core_theme):
    keywords = []
    if isinstance(core_theme, str):
        themes = [t.strip() for t in core_theme.split(',') if t.strip()]
        for theme in themes:
            keywords.append(theme)
            if '指数函数' in theme:
                keywords.extend(['指数函数', '指数', 'exponential'])
            elif '幂函数' in theme:
                keywords.extend(['幂函数', '幂'])
            elif '对数函数' in theme:
                keywords.extend(['对数函数', '对数', 'log'])
            elif '三角函数' in theme:
                keywords.extend(['三角函数', '三角', 'sin', 'cos', 'tan'])
            else:
                import jieba
                jieba_keywords = list(jieba.cut(theme))
                keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
    return list(set(keywords))


def _score_by_semantic_requirements(doc, meta, requirements):
    """
    根据用户的语义要求评分（资源类型感知）
    
    Args:
        doc: 文档内容
        meta: 文档元数据（包含resource_type）
        requirements: 用户要求列表（如 ["互动性强", "生动有趣"]）
    
    Returns:
        语义匹配分数 (0-1)
    """
    if not requirements:
        return 0.5  # 默认中性分数
    
    total_score = 0.0
    for req in requirements:
        # 使用资源类型感知的语义匹配
        similarity = semantic_matcher.calculate_similarity_with_resource_type(req, doc, meta)
        total_score += similarity
    
    return total_score / len(requirements) if requirements else 0.5


def _sort_results_by_semantic_score(results, requirements):
    """
    根据语义匹配分数排序结果
    
    Args:
        results: 检索结果
        requirements: 用户要求列表
    
    Returns:
        排序后的结果
    """
    if not requirements or not results.get("documents") or not results["documents"][0]:
        print(f"   ⚠️ 语义排序跳过: requirements={requirements}, 结果数量={len(results.get('documents', [[]])[0]) if results else 0}")
        return results
    
    print(f"\n   📊 [语义匹配调试] 开始语义排序，要求: {requirements}")
    print(f"   📊 [语义匹配调试] 待排序资源数量: {len(results['documents'][0])}")
    
    # 创建带语义分数的列表
    scored_items = []
    for i, (doc, meta, dist, id_) in enumerate(zip(
        results["documents"][0], 
        results["metadatas"][0], 
        results["distances"][0], 
        results["ids"][0]
    )):
        semantic_score = _score_by_semantic_requirements(doc, meta, requirements)
        title = meta.get('title', '')[:50] if meta.get('title') else '无标题'
        print(f"   📊 [语义匹配调试] 资源{i+1}: '{title}' | 语义分数: {semantic_score:.4f} | 距离: {dist:.4f}")
        scored_items.append({
            "doc": doc,
            "meta": meta,
            "dist": dist,
            "id": id_,
            "semantic_score": semantic_score
        })
    
    # 按语义分数排序（降序），同时考虑距离（升序）
    scored_items.sort(key=lambda x: (-x["semantic_score"], x["dist"]))
    
    print(f"\n   📊 [语义匹配调试] 排序后顺序:")
    for i, item in enumerate(scored_items[:5]):  # 只显示前5个
        title = item["meta"].get('title', '')[:50] if item["meta"].get('title') else '无标题'
        print(f"   📊 [语义匹配调试] 排名{i+1}: '{title}' | 语义分数: {item['semantic_score']:.4f}")
    
    # 重新组装结果
    sorted_results = {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
        "ids": [[]]
    }
    
    for item in scored_items:
        sorted_results["documents"][0].append(item["doc"])
        sorted_results["metadatas"][0].append(item["meta"])
        sorted_results["distances"][0].append(item["dist"])
        sorted_results["ids"][0].append(item["id"])
    
    print(f"   ✅ [语义匹配调试] 语义排序完成")
    return sorted_results
