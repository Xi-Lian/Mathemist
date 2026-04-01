from .._shared import *

EXPLICIT_EXERCISE_QUERY_KEYWORDS = [
    "习题",
    "题目",
    "练习题",
    "练习",
    "测试题",
    "选择题",
    "填空题",
    "解答题",
    "证明题",
]
GENERAL_MATERIAL_QUERY_KEYWORDS = ["资料", "学习资料", "教学资源", "教学资料", "资源", "内容"]
STRONG_EXERCISE_MARKERS = [
    "选择题",
    "填空题",
    "解答题",
    "证明题",
    "答案",
    "解析",
    "题目类型",
]
CATEGORY_ALIASES = {
    "lesson_plan": "lesson_plan",
    "lesson_plan_patterns": "lesson_plan",
    "syllabus": "syllabus",
    "syllabus_resources": "syllabus",
    "lesson_case": "lesson_case",
    "lesson_case_resources": "lesson_case",
    "exercise": "exercise",
    "exercise_resources": "exercise",
    "courseware": "courseware",
    "courseware_resources": "courseware",
    "ggb": "ggb",
    "visualization": "visualization",
    "visualization_examples": "visualization",
    "theory": "theory",
    "theory_resources": "theory",
}


def _contains_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in (text or "") for keyword in keywords)


def _is_general_material_query(query: str) -> bool:
    return _contains_any(query, GENERAL_MATERIAL_QUERY_KEYWORDS) and not _contains_any(query, EXPLICIT_EXERCISE_QUERY_KEYWORDS)


def _looks_like_exercise(content: str, metadata: Dict[str, Any]) -> bool:
    exercise_type = metadata.get("题目类型", "") or ""
    if exercise_type:
        return True

    text = f"{content or ''} {metadata.get('title', '')} {metadata.get('source_file', '')}"
    marker_count = sum(1 for keyword in STRONG_EXERCISE_MARKERS if keyword in text)
    return marker_count >= 2


class _DynamicClassifyResourceMixin:
    def _dynamic_classify_resource(self, resource: Dict[str, Any], content: str, metadata: Dict[str, Any], query: str) -> Optional[str]:
        """
        动态分类资源
        V54.0改进：添加对教学大纲和课例视频的支持
        
        Args:
            resource: 资源对象
            content: 资源内容
            metadata: 资源元数据
            query: 用户查询
        
        Returns:
            动态分类结果
        """
        source_file = metadata.get("source_file", "")
        file_path = metadata.get("file_path", "")
        title = metadata.get("title", "")
        is_general_material_query = _is_general_material_query(query)

        # 1. 优先相信元数据/路径，这是最稳定的信息源。
        stable_text = f"{source_file} {file_path} {title}"
        if "教学大纲" in stable_text:
            return "syllabus"
        if "教案" in stable_text:
            return "lesson_plan"
        if "课例" in stable_text or "课堂实录" in stable_text or "教学视频" in stable_text:
            return "lesson_case"
        if "课件" in stable_text or "PPT" in stable_text or "幻灯片" in stable_text or "演示文稿" in stable_text:
            return "courseware"
        if "ggb" in stable_text.lower() or "GeoGebra" in stable_text or "几何画板" in stable_text:
            return "ggb"
        if "习题" in stable_text:
            return "exercise"

        # 2. 内容分类保守处理，避免因为出现“题目/练习”就把资料打成习题。
        if "教案" in content or "教学目标" in content or "教学过程" in content:
            return "lesson_plan"
        if "教学大纲" in content or "教学任务" in content:
            return "syllabus"
        if "课例" in content or "课堂实录" in content or "教学视频" in content:
            return "lesson_case"
        if "课件" in content or "PPT" in content or "幻灯片" in content:
            return "courseware"
        if "GeoGebra" in content or "ggb" in content.lower() or "几何画板" in content:
            return "ggb"
        if ("可视化" in content or "图表" in content or "图像" in content) and not _looks_like_exercise(content, metadata):
            return "visualization"
        if not is_general_material_query and _looks_like_exercise(content, metadata):
            return "exercise"

        # 3. 基于主题兜底，但只返回数据库标准类型。
        detected_themes = self.theme_matcher.dynamic_theme_detection(content, title)
        if detected_themes:
            primary_theme = detected_themes[0]["theme"]
            if "函数" in primary_theme and not _looks_like_exercise(content, metadata):
                return "theory"

        # 4. 查询层只做轻量约束，不再强行改类。
        if "教案" in query and ("教案" in content or "教学" in content):
            return "lesson_plan"
        if ("教学大纲" in query or "课程标准" in query) and ("教学大纲" in content or "教学任务" in content):
            return "syllabus"
        if ("课例" in query or "教学视频" in query) and ("课例" in content or "课堂实录" in content or "教学视频" in content):
            return "lesson_case"
        if "课件" in query and ("课件" in content or "PPT" in content):
            return "courseware"
        if _contains_any(query, EXPLICIT_EXERCISE_QUERY_KEYWORDS) and _looks_like_exercise(content, metadata):
            return "exercise"

        normalized = CATEGORY_ALIASES.get(resource.get("resource_type", ""))
        if normalized:
            return normalized
        return None
