from ..._shared import *

BROAD_THEME_HINTS = {
    "函数",
    "数学",
    "代数",
    "几何",
    "统计",
    "概率",
    "函数的概念",
    "函数的性质",
    "函数应用",
}


def build_match_result(matched_themes, core_theme_match, related_themes, is_core_match, match_level, domain, explanation, should_show, relevance_score):
    return {
        "matched_themes": matched_themes,
        "core_theme_match": core_theme_match,
        "related_themes": related_themes,
        "mentioned_themes": [],
        "is_core_match": is_core_match,
        "match_level": match_level,
        "domain": domain,
        "explanation": explanation,
        "should_show": should_show,
        "relevance_score": relevance_score,
        "overall_score": relevance_score,
        "resource_quality": 0.5,
        "content_completeness": 0.5,
        "teaching_value": 0.5,
        "comprehensiveness": 0.5,
        "concept_hierarchy_factor": 0.5,
    }


def build_no_core_theme_result(base_relevance, resource_type):
    min_relevance_threshold = 0.10 if resource_type == "courseware" else 0.30
    print(f"   🔍 V53.13调试 - base_relevance: {base_relevance:.4f}, threshold: {min_relevance_threshold}, resource_type: {resource_type}")
    should_show = base_relevance >= min_relevance_threshold
    relevance_score = base_relevance if should_show else 0.0
    return {
        "matched_themes": [],
        "core_theme_match": None,
        "related_themes": [],
        "mentioned_themes": [],
        "is_core_match": False,
        "match_level": "none",
        "domain": "未知",
        "explanation": "未匹配到主题",
        "should_show": should_show,
        "relevance_score": relevance_score,
        "overall_score": relevance_score,
        "resource_quality": 0.5 if should_show else 0.0,
        "content_completeness": 0.3 if should_show else 0.0,
        "teaching_value": 0.15 if should_show else 0.0,
        "comprehensiveness": 0.2 if should_show else 0.0,
        "concept_hierarchy_factor": 0.5,
    }


def is_specific_theme_query(core_theme):
    themes = [theme.strip() for theme in (core_theme or "").split(",") if theme.strip()]
    if not themes:
        return False
    return any(theme not in BROAD_THEME_HINTS for theme in themes)


def has_theme_text_hit(core_theme, metadata, text):
    themes = [theme.strip() for theme in (core_theme or "").split(",") if theme.strip()]
    if not themes:
        return False

    title = metadata.get("title", "") or ""
    source_file = metadata.get("source_file", "") or ""
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "") or ""
    haystack = f"{title} {source_file} {knowledge_tags} {text or ''}"
    return any(theme in haystack for theme in themes)
