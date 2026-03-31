from .._shared import *


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

    print(f"   🔍 调试 - 资源类型: {resource_types}")
    if has_specific_resource_types(resource_types):
        db_types = []
        for user_type in resource_types:
            mapped_db_type = get_db_type(user_type)
            print(f"   🔍 调试 - 资源类型映射: {user_type} -> {mapped_db_type}")
            if mapped_db_type:
                db_types.append(mapped_db_type)

        print(f"   🔍 调试 - 数据库类型: {db_types}")
        if len(db_types) > 1:
            print("   📋 V54.0组合资源查询: 为每种资源类型单独检索")
            print(f"   🔍 V56.4调试 - 为每种资源类型创建过滤条件: {db_types}")
            for db_type in db_types:
                resource_type_filters.append({"resource_type": db_type})
        elif db_types:
            where_filter = {"resource_type": db_types[0]}
            print(f"   📋 资源类型过滤: {db_types[0]}")
        else:
            print("   ⚠️ V54.0调试 - db_types为空，无法创建资源类型过滤条件")
    elif question_type == "证明题" and ("单调性" in query or "单调" in query):
        where_filter = {"resource_type": "exercise"}
        print("   📋 V46.1单调性证明题：强制添加exercise过滤")
    elif question_type == "选择题" and any(keyword in query for keyword in ["函数", "二次函数", "三角函数"]):
        where_filter = {"resource_type": "exercise"}
        print("   📋 V48.0函数选择题：强制添加exercise过滤")
    elif any(kw in query for kw in EXERCISE_HINT_KEYWORDS) and not any(
        kw in query for kw in SPECIAL_RESOURCE_TYPE_KEYWORDS
    ):
        where_filter = {"resource_type": "exercise"}
        print("   📋 V52.0习题查询：强制添加exercise过滤")

    return resource_type_filters, where_filter


def simplify_themes(core_themes):
    themes_to_search = []
    for theme in core_themes:
        if "的应用" in theme and theme != "函数的应用":
            base_theme = theme.replace("的应用", "")
            themes_to_search.append(base_theme)
            print(f"   📝 V52.0简化主题: '{theme}' -> '{base_theme}'")
        else:
            themes_to_search.append(theme)

    print(f"   📝 V52.0使用简化主题进行检索: {themes_to_search}")

    specific_themes = []
    generic_themes_list = []
    for theme in themes_to_search:
        if theme in ["函数", "数学", "教学"]:
            generic_themes_list.append(theme)
        else:
            specific_themes.append(theme)

    if specific_themes:
        print(f"   📝 V15.1优先检索具体主题: {specific_themes}")
        if generic_themes_list:
            print(f"   📝 V15.1保留通用主题作为补充: {generic_themes_list}")

    return themes_to_search


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
    n_results_per_theme = retriever._adjust_retrieval_count(query, detected_intents, base_count)

    if len(themes_to_search) > 1:
        n_results_per_theme = min(max(n_results_per_theme, 500), 700)
        print(f"   🔍 V52.0多主题查询: 增加检索数量到 {n_results_per_theme}")

    if any(prop in theme for prop in ["函数的单调性", "函数的奇偶性", "函数的周期性"]):
        n_results_per_theme = min(max(n_results_per_theme, 600), 800)
        print(f"   🔍 函数性质查询: 增加检索数量到 {n_results_per_theme}")

    if question_type == "证明题" and ("单调性" in theme or "单调" in query):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V46.0单调性证明题: 增加检索数量到 {n_results_per_theme}")
    elif question_type == "选择题" and ("函数" in theme or "函数" in query):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V48.0函数选择题: 增加检索数量到 {n_results_per_theme}")
    elif question_type == "选择题" and ("二次函数" in theme or "二次函数" in query):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V48.0二次函数选择题: 增加检索数量到 {n_results_per_theme}")
    elif ("三角函数" in theme or "三角函数" in query) and any(kw in query for kw in ["习题", "题目", "练习题"]):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V48.0三角函数习题: 增加检索数量到 {n_results_per_theme}")
    elif ("高二" in query or "高中" in query) and ("三角函数" in theme or "三角函数" in query):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V48.0高二三角函数习题: 增加检索数量到 {n_results_per_theme}")
    elif any(kw in query for kw in ["应用题", "实际应用", "生活应用"]):
        n_results_per_theme = max(n_results_per_theme, 600)
        print(f"   🔍 V52.0应用题查询: 增加检索数量到 {n_results_per_theme}")
    elif "教案" in query or (resource_types and "教案" in resource_types):
        n_results_per_theme = max(n_results_per_theme, 500)
        print(f"   🔍 V54.0教案查询: 增加检索数量到 {n_results_per_theme}")
    elif "课件" in query or (resource_types and "课件" in resource_types):
        n_results_per_theme = max(n_results_per_theme, 900)
        print(f"   🔍 课件查询: 增加检索数量到 {n_results_per_theme}")

    return n_results_per_theme


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
    n_results_adjusted = retriever._adjust_retrieval_count(query_to_use, detected_intents, n_results_per_query, resource_types)

    if core_theme:
        n_results_adjusted = max(n_results_adjusted, 50)
        print(f"   🔍 V51.0核心主题查询: 增加检索数量到 {n_results_adjusted}")

    if (question_type == "证明题" and "单调性" in query) or ("证明" in query and "单调性" in query):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V46.0单调性证明题后备: 增加检索数量到 {n_results_adjusted}")
    elif (question_type == "证明题" and "奇偶性" in query) or ("证明" in query and "奇偶性" in query):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V50.0奇偶性证明题后备: 增加检索数量到 {n_results_adjusted}")
    elif question_type == "选择题" and ("函数" in query or "函数" in query_to_use):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V48.0函数选择题后备: 增加检索数量到 {n_results_adjusted}")
    elif question_type == "选择题" and ("二次函数" in query or "二次函数" in query_to_use):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V48.0二次函数选择题后备: 增加检索数量到 {n_results_adjusted}")
    elif ("三角函数" in query or "三角函数" in query_to_use) and any(kw in query for kw in ["习题", "题目", "练习题"]):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V48.0三角函数习题后备: 增加检索数量到 {n_results_adjusted}")
    elif ("高二" in query or "高中" in query) and ("三角函数" in query or "三角函数" in query_to_use):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V48.0高二三角函数习题后备: 增加检索数量到 {n_results_adjusted}")
    elif any(kw in query for kw in ["应用题", "实际应用", "生活应用", "例子", "实例", "案例"]):
        n_results_adjusted = max(n_results_adjusted, 600)
        print(f"   🔍 V52.0应用题/例子: 增加检索数量到 {n_results_adjusted}")
    elif "教案" in query or (resource_types and "教案" in resource_types):
        n_results_adjusted = max(n_results_adjusted, 500)
        print(f"   🔍 V54.0教案查询: 增加检索数量到 {n_results_adjusted}")
    else:
        print(f"   🔍 V46.0调试: 条件不满足，使用默认检索数量 {n_results_adjusted}")

    return n_results_adjusted
