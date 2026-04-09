from ..._shared import *
from .common import build_match_result, has_theme_text_hit, is_specific_theme_query


def evaluate_non_exercise_match(retriever, doc, metadata, base_relevance, resource_type, core_theme):
    theme_matcher_v90 = get_theme_matcher_v90()
    specific_theme_query = is_specific_theme_query(core_theme)

    if resource_type == "lesson_plan":
        precise_match_result = theme_matcher_v90.calculate_precise_match(
            query=core_theme,
            lesson_title=metadata.get("title", ""),
            lesson_content=doc,
            metadata=metadata,
        )
        # 对 V90 主题体系未覆盖的新板块，允许基于标题/路径/标签/正文的直接命中兜底展示。
        if specific_theme_query and not precise_match_result["is_core_match"] and has_theme_text_hit(core_theme, metadata, doc):
            precise_match_result["matched_themes"] = [theme for theme in core_theme.split(",") if theme.strip()]
            precise_match_result["core_theme"] = precise_match_result["matched_themes"][0] if precise_match_result["matched_themes"] else core_theme
            precise_match_result["related_themes"] = precise_match_result["matched_themes"][1:] if len(precise_match_result["matched_themes"]) > 1 else []
            precise_match_result["is_core_match"] = True
            precise_match_result["match_level"] = "core"
            precise_match_result["should_show"] = True
            precise_match_result["relevance_score"] = max(precise_match_result.get("relevance_score", 0.0), 0.85)
            precise_match_result["overall_score"] = max(precise_match_result.get("overall_score", 0.0), precise_match_result["relevance_score"])
            precise_match_result["explanation"] = f"文本直接命中主题：{core_theme}"
        if specific_theme_query and not precise_match_result["is_core_match"] and precise_match_result["match_level"] not in {"related", "extended"}:
            precise_match_result["should_show"] = False
            precise_match_result["relevance_score"] = 0.0
            precise_match_result["overall_score"] = 0.0
            precise_match_result["match_level"] = "none"
            precise_match_result["explanation"] = f"明确主题查询未命中主题：{core_theme}"
        return {
            "matched_themes": precise_match_result["matched_themes"],
            "core_theme_match": precise_match_result["core_theme"],
            "related_themes": precise_match_result["related_themes"],
            "mentioned_themes": precise_match_result["mentioned_themes"],
            "is_core_match": precise_match_result["is_core_match"],
            "match_level": precise_match_result["match_level"],
            "domain": precise_match_result["domain"],
            "explanation": precise_match_result["explanation"],
            "should_show": precise_match_result["should_show"],
            "relevance_score": precise_match_result["relevance_score"],
            "overall_score": precise_match_result.get("overall_score", precise_match_result["relevance_score"]),
            "resource_quality": precise_match_result.get("resource_quality", None),
            "content_completeness": precise_match_result.get("content_completeness", None),
            "teaching_value": precise_match_result.get("teaching_value", None),
            "comprehensiveness": precise_match_result.get("comprehensiveness", None),
            "concept_hierarchy_factor": precise_match_result.get("concept_hierarchy_factor", 0.5),
        }

    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    matched_themes = [theme for theme in query_themes if theme in doc or theme in metadata.get("title", "")]
    theme_keywords = []
    for theme in query_themes:
        theme_keywords.extend(retriever.config_loader.get_theme_keywords(theme))
    matched_keywords = [keyword for keyword in theme_keywords if keyword in doc or keyword in metadata.get("title", "")]

    if resource_type in {"courseware", "exercise"}:
        return evaluate_keyword_based_match(base_relevance, resource_type, query_themes, matched_keywords, theme_keywords)
    if matched_themes:
        return build_match_result(matched_themes, matched_themes[0], matched_themes[1:] if len(matched_themes) > 1 else [], True, "core", resource_type, f"匹配到主题: {', '.join(matched_themes)}", True, base_relevance)
    if specific_theme_query and not has_theme_text_hit(core_theme, metadata, doc):
        return build_match_result([], None, [], False, "none", resource_type, f"明确主题查询未命中主题：{core_theme}", False, 0.0)
    return build_match_result([], None, [], False, "related", resource_type, "基于向量相似度匹配", base_relevance > 0.30, base_relevance * 0.5)


def evaluate_keyword_based_match(base_relevance, resource_type, query_themes, matched_keywords, theme_keywords):
    specific_theme_query = is_specific_theme_query(",".join(query_themes))
    if resource_type == "courseware":
        print(f"   🔍 V90.2课件资源调试 - base_relevance: {base_relevance:.4f}, matched_keywords: {matched_keywords}, theme_keywords: {theme_keywords}")
    if matched_keywords:
        keyword_match_score = min(len(matched_keywords) / max(len(theme_keywords), 1), 1.0)
        should_show = keyword_match_score >= (0.2 if resource_type == "courseware" else 0.3)
        if resource_type == "courseware":
            print(f"   🔍 V90.2课件资源 - 匹配到关键词: {keyword_match_score:.4f} >= 0.2, should_show: {should_show}")
        return build_match_result(
            query_themes,
            query_themes[0] if query_themes else None,
            query_themes[1:] if len(query_themes) > 1 else [],
            True,
            "core",
            resource_type,
            f"匹配到主题关键词: {', '.join(matched_keywords[:5])}",
            should_show,
            base_relevance * (0.7 + 0.3 * keyword_match_score),
        )
    if specific_theme_query:
        return build_match_result([], None, [], False, "none", resource_type, "明确主题查询未命中主题关键词", False, 0.0)
    should_show = base_relevance > (0.10 if resource_type == "courseware" else 0.30)
    if resource_type == "courseware":
        print(f"   🔍 V90.2课件资源 - 基础相关性: {base_relevance:.4f} > 0.10, should_show: {should_show}")
    return build_match_result([], None, [], False, "related", resource_type, "基于向量相似度匹配", should_show, base_relevance * 0.5)
