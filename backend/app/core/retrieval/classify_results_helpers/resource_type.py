from .._shared import *


GENERAL_RESOURCE_TYPES = {"资料", "资源", "教学资源", "教学资料"}


def init_classified():
    return {
        "theory_resources": [],
        "lesson_plan_patterns": [],
        "exercise_resources": [],
        "visualization_examples": [],
        "general_resources": [],
        "courseware_resources": [],
        "lesson_case_resources": [],
        "ggb_resources": [],
        "syllabus_resources": [],
    }


def normalize_resource_type(metadata, resource_type):
    source_file = metadata.get("source_file", "")
    if "习题" in source_file and resource_type != "exercise":
        resource_type = "exercise"
        print(f"   🔍 V19.5调试 - 根据source_file判断为习题资源: '{source_file}'")
    elif "教案" in source_file and resource_type != "lesson_plan":
        resource_type = "lesson_plan"
        print(f"   🔍 V53.6调试 - 根据source_file判断为教案资源: '{source_file}'")
    elif "教学大纲" in source_file and resource_type != "syllabus":
        resource_type = "syllabus"
        print(f"   🔍 V53.6调试 - 根据source_file判断为教学大纲资源: '{source_file}'")
    elif "ggb" in source_file.lower() and resource_type != "ggb":
        resource_type = "ggb"
        print(f"   🔍 V53.6调试 - 根据source_file判断为GGB资源: '{source_file}'")
    elif any(keyword in source_file for keyword in ["课件", "PPT", "幻灯片", "演示文稿"]) and resource_type != "courseware":
        resource_type = "courseware"
        print(f"   🔍 V85.0调试 - 根据source_file判断为课件资源: '{source_file}'")
    return resource_type


def matches_requested_resource_type(resource_type, resource_types):
    print(f"   🔍 V53.7调试 - resource_types: {resource_types}, standard_types: {[get_standard_name(rt) for rt in resource_types] if resource_types else []}")
    if not resource_types:
        print("   ✅ V53.7调试 - 跳过资源类型过滤: resource_types为空或包含通用类型")
        return True

    standard_types = [get_standard_name(rt) for rt in resource_types]
    if any(rt in GENERAL_RESOURCE_TYPES for rt in resource_types) or any(st == "资料" for st in standard_types):
        print("   ✅ V53.7调试 - 跳过资源类型过滤: resource_types为空或包含通用类型")
        return True

    mapped_db_types = []
    resource_type_matched = False
    for user_type in resource_types:
        mapped_db_type = get_db_type(user_type)
        if mapped_db_type:
            mapped_db_types.append(mapped_db_type)

        mapping = get_resource_type_mapping(user_type)
        if not mapping:
            continue

        standard_name = mapping[0]
        db_type = mapping[1]
        if resource_type == db_type:
            resource_type_matched = True
            print(f"   ✅ V80.0调试 - 资源类型匹配: {resource_type} 等于映射后的数据库类型 {db_type}")
            break
        if resource_type == user_type:
            resource_type_matched = True
            print(f"   ✅ V80.0调试 - 资源类型匹配: {resource_type} 等于用户输入的资源类型 {user_type}")
            break
        if resource_type == standard_name:
            resource_type_matched = True
            print(f"   ✅ V82.0调试 - 资源类型匹配: {resource_type} 等于标准名称 {standard_name}")
            break
        if _matches_special_alias(user_type, resource_type):
            resource_type_matched = True
            break

    print(f"   🔍 V73.0调试 - 映射后的数据库类型: {mapped_db_types}")
    if not resource_type_matched:
        print(f"   ⚠️ V80.0调试 - 资源类型不匹配: {resource_type} 不在映射后的数据库类型列表 {mapped_db_types} 中，也不等于用户输入的资源类型 {resource_types}")
        if resource_types:
            print("   📋 V71.0改进：没有匹配的资源类型，尝试不进行资源类型过滤")
            return True
    return True if resource_type_matched else False


def _matches_special_alias(user_type, resource_type):
    if any(keyword in user_type for keyword in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"]) and resource_type == "courseware":
        print(f"   ✅ V86.0调试 - 课件资源类型匹配: {resource_type} 等于courseware")
        return True
    if any(keyword in user_type for keyword in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"]) and resource_type == "lesson_plan":
        print(f"   ✅ V86.0调试 - 教案资源类型匹配: {resource_type} 等于lesson_plan")
        return True
    if any(keyword in user_type for keyword in ["课例", "教学视频", "课堂实录", "视频课"]) and resource_type == "lesson_case":
        print(f"   ✅ V91.0调试 - 课例资源类型匹配: {resource_type} 等于lesson_case")
        return True
    if any(keyword in user_type for keyword in ["GGB", "GeoGebra", "动态图", "可视化", "几何画板"]) and resource_type == "ggb":
        print(f"   ✅ V91.0调试 - GGB资源类型匹配: {resource_type} 等于ggb")
        return True
    if any(keyword in user_type for keyword in ["教学大纲", "大纲", "课程标准", "课程大纲"]) and resource_type == "syllabus":
        print(f"   ✅ V91.0调试 - 教学大纲资源类型匹配: {resource_type} 等于syllabus")
        return True
    if any(keyword in user_type for keyword in ["理论", "知识点", "概念", "基础知识"]) and resource_type == "theory":
        print(f"   ✅ V91.0调试 - 理论资源类型匹配: {resource_type} 等于theory")
        return True
    if any(keyword in user_type for keyword in ["图像", "图形", "例子", "可视化", "图表"]) and resource_type == "visualization":
        print(f"   ✅ V91.0调试 - 可视化资源类型匹配: {resource_type} 等于visualization")
        return True
    return False


def add_high_relevance_resource(classified, metadata, doc, relevance, resource_type):
    resource = {
        "title": metadata.get("title", "未知"),
        "content": doc,
        "source": metadata.get("source_file", ""),
        "relevance": relevance,
        "metadata": metadata,
        "base_relevance": relevance,
        "theme_match": False,
        "type_match": False,
        "matched_theme_count": 0,
        "theme_boost": 0.0,
        "conflict_theme": False,
        "matched_themes": [],
        "is_comprehensive": False,
        "难度": metadata.get("难度", "") or metadata.get("difficulty", "") or metadata.get("难度（1-5）", ""),
        "题目类型": metadata.get("题目类型", ""),
        "知识点": metadata.get("知识点", "") or metadata.get("知识点标签", ""),
    }
    category_map = {
        "lesson_plan": "lesson_plan_patterns",
        "visualization": "visualization_examples",
        "exercise": "exercise_resources",
        "courseware": "courseware_resources",
        "lesson_case": "lesson_case_resources",
        "ggb": "ggb_resources",
        "syllabus": "syllabus_resources",
        "theory": "theory_resources",
    }
    classified[category_map.get(resource_type, "theory_resources")].append(resource)
