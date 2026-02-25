"""
资源类型映射配置（集中管理）

职责：
- 统一管理所有资源类型的映射关系
- 用户输入词 -> 标准类型 -> 数据库类型 -> 响应字段

设计原则：
1. 用户友好：支持多种同义词输入
2. 集中管理：所有映射在一个地方
3. 易于扩展：添加新类型只需修改此文件
4. 便于调试：包含详细的类型信息
"""

# 统一的资源类型映射表
# 结构：{用户输入词: (标准名称, 数据库类型, 响应字段, 图标)}
RESOURCE_TYPE_MAPPING = {
    "教案": ("教案", "lesson_plan", "lesson_plan_patterns", "📚"),
    "教学设计": ("教案", "lesson_plan", "lesson_plan_patterns", "📚"),
    "教学方案": ("教案", "lesson_plan", "lesson_plan_patterns", "📚"),
    
    "课件": ("课件", "courseware", "courseware_resources", "📊"),
    "PPT": ("课件", "courseware", "courseware_resources", "📊"),
    "幻灯片": ("课件", "courseware", "courseware_resources", "📊"),
    
    "课例": ("课例", "lesson_case", "lesson_case_resources", "🎬"),
    "教学视频": ("课例", "lesson_case", "lesson_case_resources", "🎬"),
    "课堂实录": ("课例", "lesson_case", "lesson_case_resources", "🎬"),
    
    "习题": ("习题", "exercise", "exercise_resources", "📝"),
    "题目": ("习题", "exercise", "exercise_resources", "📝"),
    "练习": ("习题", "exercise", "exercise_resources", "📝"),
    "测试": ("习题", "exercise", "exercise_resources", "📝"),
    
    "GGB": ("GGB", "ggb", "ggb_resources", "🔧"),
    "GeoGebra": ("GGB", "ggb", "ggb_resources", "🔧"),
    "动态图": ("GGB", "ggb", "ggb_resources", "🔧"),
    "可视化": ("GGB", "ggb", "ggb_resources", "🔧"),
    
    "教学大纲": ("教学大纲", "syllabus", "syllabus_resources", "📋"),
    "大纲": ("教学大纲", "syllabus", "syllabus_resources", "📋"),
    "课程标准": ("教学大纲", "syllabus", "syllabus_resources", "📋"),
    
    "理论": ("理论", "theory", "theory_resources", "📖"),
    "知识点": ("理论", "theory", "theory_resources", "📖"),
    "概念": ("理论", "theory", "theory_resources", "📖"),
    
    "资料": ("资料", "all", "all_resources", "📂"),
    "资源": ("资料", "all", "all_resources", "📂"),
    
    "图像": ("可视化", "visualization", "visualization_examples", "🎨"),
    "图形": ("可视化", "visualization", "visualization_examples", "🎨"),
    "例子": ("可视化", "visualization", "visualization_examples", "🎨")
}

# 数据库类型到标准名称的映射（反向映射）
DB_TYPE_TO_STANDARD = {
    "lesson_plan": "教案",
    "courseware": "课件",
    "lesson_case": "课例",
    "exercise": "习题",
    "ggb": "GGB",
    "syllabus": "教学大纲",
    "theory": "理论",
    "visualization": "可视化"
}


def get_resource_type_mapping(user_type: str) -> tuple:
    """
    获取资源类型映射信息
    
    Args:
        user_type: 用户输入的资源类型
    
    Returns:
        (标准名称, 数据库类型, 响应字段, 图标)
        如果找不到映射，返回None
    """
    return RESOURCE_TYPE_MAPPING.get(user_type)


def get_db_type(user_type: str) -> str:
    """
    获取数据库类型
    
    Args:
        user_type: 用户输入的资源类型
    
    Returns:
        数据库类型，如果找不到映射返回None
    """
    mapping = get_resource_type_mapping(user_type)
    return mapping[1] if mapping else None


def get_response_field(user_type: str) -> str:
    """
    获取响应字段
    
    Args:
        user_type: 用户输入的资源类型
    
    Returns:
        响应字段名，如果找不到映射返回None
    """
    mapping = get_resource_type_mapping(user_type)
    return mapping[2] if mapping else None


def get_icon(user_type: str) -> str:
    """
    获取图标
    
    Args:
        user_type: 用户输入的资源类型
    
    Returns:
        图标，如果找不到映射返回空字符串
    """
    mapping = get_resource_type_mapping(user_type)
    return mapping[3] if mapping else ""


def get_standard_name(user_type: str) -> str:
    """
    获取标准名称
    
    Args:
        user_type: 用户输入的资源类型
    
    Returns:
        标准名称，如果找不到映射返回原始类型
    """
    mapping = get_resource_type_mapping(user_type)
    return mapping[0] if mapping else user_type


def get_all_user_types() -> list:
    """
    获取所有支持的用户输入类型
    
    Returns:
        用户输入类型列表
    """
    return list(RESOURCE_TYPE_MAPPING.keys())


def get_all_standard_types() -> list:
    """
    获取所有标准类型
    
    Returns:
        标准类型列表（去重）
    """
    return list({v[0] for v in RESOURCE_TYPE_MAPPING.values()})


def get_all_db_types() -> list:
    """
    获取所有数据库类型
    
    Returns:
        数据库类型列表（去重）
    """
    return list({v[1] for v in RESOURCE_TYPE_MAPPING.values()})


def normalize_resource_types(user_types: list) -> list:
    """
    规范化资源类型列表
    
    Args:
        user_types: 用户输入的资源类型列表
    
    Returns:
        规范化后的类型列表（去重）
    """
    normalized = []
    for user_type in user_types:
        std_name = get_standard_name(user_type)
        if std_name not in normalized:
            normalized.append(std_name)
    return normalized


def print_mapping_summary():
    """
    打印映射关系摘要（用于调试）
    """
    print("=" * 80)
    print("资源类型映射配置摘要")
    print("=" * 80)
    
    print(f"\n📊 统计:")
    print(f"   总用户输入类型: {len(RESOURCE_TYPE_MAPPING)}")
    print(f"   标准类型数量: {len(get_all_standard_types())}")
    print(f"   数据库类型数量: {len(get_all_db_types())}")
    
    print(f"\n📋 按标准类型分组:")
    std_types = get_all_standard_types()
    for std_type in sorted(std_types):
        user_types = [k for k, v in RESOURCE_TYPE_MAPPING.items() if v[0] == std_type]
        db_type = [v[1] for k, v in RESOURCE_TYPE_MAPPING.items() if v[0] == std_type][0]
        icon = [v[3] for k, v in RESOURCE_TYPE_MAPPING.items() if v[0] == std_type][0]
        print(f"\n   {icon} {std_type} (数据库: {db_type})")
        print(f"      用户输入词: {', '.join(user_types)}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_mapping_summary()
