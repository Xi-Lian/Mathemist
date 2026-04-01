from .._shared import *


NON_FUNCTION_THEMES = [
    "立体几何",
    "空间点线面",
    "空间几何体",
    "概率",
    "统计",
    "概率与统计",
    "数列",
    "不等式",
    "圆锥曲线",
    "导数",
    "向量",
    "立体几何初步",
    "空间向量",
]

FUNCTION_RELATED_THEME_NAMES = [
    "二次函数",
    "指数函数",
    "对数函数",
    "三角函数",
    "幂函数",
    "一次函数",
    "函数的概念",
    "函数应用",
    "二次函数应用",
    "三角函数应用",
    "幂函数应用",
    "指数与对数函数综合",
    "函数的零点",
    "二分法",
    "函数的单调性",
    "函数的奇偶性",
    "函数的周期性",
    "对数函数运算",
    "诱导公式",
    "三角恒等变换",
]

NON_FUNCTION_KEYWORDS = [
    "立体几何",
    "空间几何",
    "空间向量",
    "概率",
    "统计",
    "概率统计",
    "数列",
    "等差数列",
    "等比数列",
    "不等式",
    "线性规划",
    "圆锥曲线",
    "椭圆",
    "双曲线",
    "抛物线",
]


def validate_resource_types(retriever, resource_types):
    if not resource_types:
        resource_types = retriever._extract_resource_types_from_query(retriever._current_query)
        if resource_types:
            print(f"📋 自动识别资源类型: {resource_types}")

    if resource_types:
        from ....config.resource_type_config import (
            get_supported_resource_types,
            is_valid_resource_type,
        )

        invalid_types = [rt for rt in resource_types if not is_valid_resource_type(rt)]
        if invalid_types:
            print(f"⚠️ 检测到无效资源类型: {invalid_types}")
            print(f"📋 支持的资源类型: {[rt['name'] for rt in get_supported_resource_types()]}")
            resource_types = [rt for rt in resource_types if is_valid_resource_type(rt)]
            if not resource_types:
                print("❌ 没有有效的资源类型，返回空结果")
                return None, retriever._get_empty_result()
            print(f"✅ 过滤后的资源类型: {resource_types}")

    return resource_types, None


def apply_loose_mode(retriever, query, quantity_limit):
    if "还要多一点" in query or "再要一点" in query or "多一点" in query:
        print("🔍 检测到'还要一点'查询，使用宽松模式")
        if quantity_limit:
            quantity_limit *= 2
        retriever._loose_mode = True
    else:
        retriever._loose_mode = False
    return quantity_limit


def prepare_runtime_context(
    retriever,
    query,
    quantity_limit,
    grade_info,
    clarified_topic,
    difficulty_info,
):
    query_features = retriever.content_extractor.extract_query_content_features(query)
    retriever._current_query = query
    retriever._current_query_features = query_features
    retriever._current_quantity_limit = quantity_limit
    retriever._current_grade_info = grade_info
    retriever._current_clarified_topic = clarified_topic
    retriever._current_difficulty_info = difficulty_info
    retriever._current_scope_notice = None

    if query_features["has_content_requirement"]:
        print("🔍 检测到内容查询要求:")
        print(f"   - 教学方法: {query_features['required_methods']}")
        print(f"   - 教学环节: {query_features['required_stages']}")
        print(f"   - 教学手段: {query_features['required_tools']}")

    if grade_info:
        print(f"🎓 年级信息（来自意图分析）: {grade_info}")
    else:
        fallback_grade = retriever.grade_enricher.extract_grade_from_query(query)
        if fallback_grade:
            print(f"🎓 年级解析（回退）: {fallback_grade}")
            retriever._current_grade_info = fallback_grade
        else:
            print("🎓 年级解析: 未检测到年级信息")

    subjective_intent = retriever.subjective_interpreter.interpret(query)
    if subjective_intent:
        print("💭 主观意图解析:")
        print(f"   - 主观词汇: {subjective_intent.get('subjective_words', [])}")
        print(f"   - 难度范围: {subjective_intent.get('difficulty_range', None)}")
        print(f"   - 认知层次: {subjective_intent.get('cognitive_level', [])}")
        print(f"   - 用户场景: {subjective_intent.get('user_scenario', None)}")
        retriever._current_subjective_intent = subjective_intent
    else:
        print("💭 主观意图解析: 未检测到主观意图")
        retriever._current_subjective_intent = None

    return query_features


def ensure_collection_ready(retriever):
    if not retriever._check_vector_db_exists():
        print("⚠️  向量数据库不存在，尝试构建...")
        if not retriever.vector_db_builder.build_vector_database():
            print("❌ 向量数据库构建失败")
            return None, retriever._get_empty_result()

    client = retriever.vector_db_builder.get_chroma_client()
    retriever.vector_db_builder.get_embedding_model()
    return client.get_collection(name=retriever.COLLECTION_NAME), None


def extract_query_context(retriever, query, quantity_limit):
    print("\n🔍 开始提取多维度查询条件...")
    query_conditions = retriever._extract_query_conditions(query)

    core_themes = query_conditions["knowledge_points"]
    core_theme = ",".join(core_themes) if core_themes else ""
    print(f"🧠 识别核心主题: {core_theme}")

    if not core_theme:
        core_theme = retriever._extract_core_theme(query)
        print(f"   📝 使用_extract_core_theme提取核心主题: '{core_theme}'")
        core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]

    scope_notice = None
    if has_non_function_theme(retriever, query, core_theme):
        scope_notice = {
            "scope": "function_only",
            "message": "当前资源库以函数板块为主，已返回最相关的函数板块资源作为降级结果。",
            "original_query": query,
            "detected_theme": core_theme,
        }
        retriever._current_scope_notice = scope_notice
        print("⚠️ 检测到非函数主题：改为降级检索，不再直接空返回")
        core_theme = ""
        core_themes = []

    question_type = query_conditions["question_type"]
    difficulty = query_conditions["difficulty"]
    grade = query_conditions["grade"]
    exam_form = query_conditions["exam_form"]
    quantity = query_conditions["quantity"]

    if quantity > 0:
        quantity_limit = quantity
        print(f"📝 使用用户指定的数量: {quantity}")

    if question_type:
        print(f"📝 提取到题目类型: {question_type}")
    if difficulty:
        print(f"📝 提取到难度: {difficulty}")
    if grade:
        print(f"📝 提取到年级: {grade}")
    if exam_form:
        print(f"📝 提取到考查形式: {exam_form}")

    return {
        "query_conditions": query_conditions,
        "core_theme": core_theme,
        "core_themes": core_themes,
        "question_type": question_type,
        "difficulty": difficulty,
        "grade": grade,
        "exam_form": exam_form,
        "quantity_limit": quantity_limit,
        "scope_notice": scope_notice,
    }, None


def has_non_function_theme(retriever, query, core_theme):
    if not core_theme:
        return False

    theme_list = [t.strip() for t in core_theme.split(",") if t.strip()]
    query_lower = query.lower()

    for theme in theme_list:
        if theme in NON_FUNCTION_THEMES:
            return True
        if theme in retriever.knowledge_hierarchy and theme not in FUNCTION_RELATED_THEME_NAMES:
            return True

    if any(keyword in query_lower for keyword in NON_FUNCTION_KEYWORDS):
        return True

    return False
