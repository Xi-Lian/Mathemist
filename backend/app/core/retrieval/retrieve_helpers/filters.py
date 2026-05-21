from .._shared import *
from app.config.resource_type_config import get_db_type
import logging
logger = logging.getLogger(__name__)


GENERAL_RESOURCE_TYPES = {"资料", "资源", "教学资源", "教学资料"}
SPECIAL_RESOURCE_TYPE_KEYWORDS = [
    "教案",
    "教学设计",
    "教学方案",
    "教学大纲",
    "大纲",
    "课程标准",
    "课件",
    "PPT",
    "幻灯片",
    "课例",
    "教学视频",
    "课堂实录",
    "GGB",
    "GeoGebra",
    "动态图",
    "可视化",
]
EXERCISE_HINT_KEYWORDS = ["习题", "题目", "练习题", "例子", "实例", "案例", "应用题", "实际应用", "生活应用"]


def has_specific_resource_types(resource_types):
    return bool(resource_types) and not any(rt in GENERAL_RESOURCE_TYPES for rt in resource_types)


def build_resource_type_filters(query, resource_types, question_type):
    resource_type_filters = []
    where_filter = None

    logger.info(f"资源类型: {resource_types}")
    if has_specific_resource_types(resource_types):
        db_types = []
        for user_type in resource_types:
            mapped_db_type = get_db_type(user_type)
            logger.info(f"资源类型映射: {user_type} -> {mapped_db_type}")
            if mapped_db_type:
                db_types.append(mapped_db_type)

        logger.info(f"数据库类型: {db_types}")
        if len(db_types) > 1:
            logger.info("组合资源查询: 为每种资源类型单独检索")
            for db_type in db_types:
                resource_type_filters.append({"resource_type": db_type})
        elif db_types:
            # V100.1新增：对于课件资源，即使只有一种也返回 resource_type_filters，以便触发精确匹配逻辑
            if "courseware" in db_types:
                logger.info("课件资源查询: 为课件单独检索以触发精确匹配")
                resource_type_filters.append({"resource_type": db_types[0]})
            else:
                where_filter = {"resource_type": db_types[0]}
                logger.info(f"资源类型过滤: {db_types[0]}")
        else:
            logger.warning("db_types为空，无法创建资源类型过滤条件")
    elif question_type in {"证明题", "选择题"}:
        where_filter = {"resource_type": "exercise"}
        logger.info("题型导向查询：使用exercise过滤")
    elif any(kw in query for kw in EXERCISE_HINT_KEYWORDS) and not any(kw in query for kw in SPECIAL_RESOURCE_TYPE_KEYWORDS):
        where_filter = {"resource_type": "exercise"}
        logger.info("习题查询：使用exercise过滤")

    return resource_type_filters, where_filter


def simplify_themes(core_themes):
    themes_to_search = []
    for theme in core_themes:
        if "的应用" in theme and theme != "函数的应用":
            base_theme = theme.replace("的应用", "")
            themes_to_search.append(base_theme)
            logger.info(f"简化主题: '{theme}' -> '{base_theme}'")
        else:
            themes_to_search.append(theme)

    themes_to_search = _deduplicate_broad_themes(themes_to_search)
    logger.info(f"使用简化主题进行检索: {themes_to_search}")
    return themes_to_search


def _deduplicate_broad_themes(themes):
    deduped = []
    for theme in themes:
        if theme not in deduped:
            deduped.append(theme)

    family_groups = [
        {"概率", "统计", "概率与统计"},
    ]
    for family in family_groups:
        present = [theme for theme in deduped if theme in family]
        if len(present) <= 1:
            continue

        preferred = None
        for candidate in present:
            if any(other != candidate and candidate in other for other in present):
                preferred = candidate
        if preferred is None:
            preferred = max(present, key=len)

        deduped = [theme for theme in deduped if theme not in family or theme == preferred]
        print(f"   🧹 合并同族宽泛主题: {present} -> 保留 '{preferred}'")

    return deduped


def _compute_retrieval_budget(base_count, multi_theme_count, resource_types):
    base = max(80, min(base_count, 200))
    if multi_theme_count > 1:
        base = min(220, base + 20)

    if resource_types and has_specific_resource_types(resource_types):
        base = min(240, base + 20)
    
    # V100.1新增：课件资源需要更多的检索结果，因为课件的向量相似度通常较低
    if resource_types and any(rt in ["课件", "PPT", "幻灯片"] for rt in resource_types):
        base = min(300, base + 60)

    return base


def adjust_multi_theme_result_count(
    retriever,
    query,
    detected_intents,
    base_count,
    themes_to_search,
    theme,
    question_type,
    resource_types,
):
    adjusted = retriever._adjust_retrieval_count(query, detected_intents, base_count)
    budget = _compute_retrieval_budget(adjusted, len(themes_to_search), resource_types)
    print(f"   📦 多主题固定预算: theme='{theme}', n_results={budget}")
    return budget


def adjust_single_theme_result_count(
    retriever,
    query,
    query_to_use,
    detected_intents,
    n_results_per_query,
    core_theme,
    question_type,
    resource_types,
):
    adjusted = retriever._adjust_retrieval_count(query_to_use, detected_intents, n_results_per_query, resource_types)
    budget = _compute_retrieval_budget(adjusted, 1, resource_types)
    print(f"   📦 单主题固定预算: n_results={budget}, core_theme='{core_theme}'")
    return budget
