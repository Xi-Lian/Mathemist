from ..._shared import *
from .common import BROAD_THEME_HINTS


def evaluate_multi_theme_match(retriever, doc, metadata, base_relevance, core_theme, multi_theme_info):
    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    specific_theme_query = any(theme not in BROAD_THEME_HINTS for theme in query_themes)
    has_query_theme_in_multi = any(qt in multi_theme_info for qt in query_themes)
    print(f"   🔍 V30.1调试: query_themes={query_themes}, multi_theme_info={multi_theme_info}, has_query_theme_in_multi={has_query_theme_in_multi}")

    if not has_query_theme_in_multi:
        print(f"   ⚠️ V30.1主题误标修复: 多主题检索结果{multi_theme_info}不包含查询主题{query_themes}，强制使用查询主题")
        matched_themes = query_themes
        relevance_score = base_relevance
        theme_distances = {}
        valid_themes = matched_themes
    else:
        matched_themes = multi_theme_info
        theme_distances = metadata.get("_theme_distances", {})
        relevance_score = 1 / (1 + (sum(theme_distances.values()) / len(theme_distances))) if theme_distances else 0.8
        valid_themes = _filter_valid_themes(retriever, doc, metadata, core_theme, matched_themes)

    if not valid_themes and matched_themes and not specific_theme_query:
        valid_themes = matched_themes[:1]
        print(f"    ⚠️ 多主题检索：无有效主题，使用备选主题: {valid_themes}")

    if not valid_themes:
        return {
            "matched_themes": [],
            "core_theme_match": None,
            "related_themes": [],
            "mentioned_themes": [],
            "is_core_match": False,
            "match_level": "none",
            "domain": "未知",
            "explanation": "多主题检索结果经排除词检查后无有效匹配",
            "should_show": False,
            "relevance_score": 0.0,
            "overall_score": 0.0,
            "resource_quality": 0.0,
            "content_completeness": 0.0,
            "teaching_value": 0.0,
            "comprehensiveness": 0.0,
            "concept_hierarchy_factor": 0.5,
        }

    if theme_distances:
        valid_theme_distances = {k: v for k, v in theme_distances.items() if k in valid_themes}
        core_theme_match = min(valid_theme_distances, key=valid_theme_distances.get) if valid_theme_distances else valid_themes[0]
    else:
        core_theme_match = valid_themes[0]

    return {
        "matched_themes": valid_themes,
        "core_theme_match": core_theme_match,
        "related_themes": [theme for theme in valid_themes if theme != core_theme_match],
        "mentioned_themes": [],
        "is_core_match": True,
        "match_level": "core",
        "domain": "多主题",
        "explanation": f"匹配到{len(valid_themes)}个主题: {', '.join(valid_themes)}",
        "should_show": True,
        "relevance_score": relevance_score,
        "overall_score": relevance_score,
        "resource_quality": 0.5,
        "content_completeness": 0.3,
        "teaching_value": 0.15,
        "comprehensiveness": 0.2,
        "concept_hierarchy_factor": 0.5,
    }


def _filter_valid_themes(retriever, doc, metadata, core_theme, matched_themes):
    theme_matcher_v90 = get_theme_matcher_v90()
    valid_themes = []
    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
    full_text = f"{metadata.get('title', '')} {doc}".lower()
    explicit_exclusion_words = ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数", "三角", "sin", "cos", "tan"]

    for theme in matched_themes:
        exclusion_words = theme_matcher_v90.theme_exclusion_words.get(theme, [])
        filtered_exclusion_words = []
        for word in exclusion_words:
            is_other_theme_keyword = any(other_theme != theme and word in other_theme for other_theme in query_themes)
            if not is_other_theme_keyword:
                filtered_exclusion_words.append(word)

        print(f"    🔍 主题 '{theme}' 的排除词: {exclusion_words}")
        print(f"    🔍 查询主题: {query_themes}")
        print(f"    🔍 过滤后的排除词: {filtered_exclusion_words}")

        has_exclusion_word = False
        for word in filtered_exclusion_words:
            if word in explicit_exclusion_words and word.lower() in full_text:
                has_exclusion_word = True
                print(f"    ⚠️ 多主题检索：'{metadata.get('title', '未知')}' 与主题 '{theme}' 不匹配（包含排除词 '{word}'）")
                break

        if has_exclusion_word:
            print(f"    ⚠️ 多主题检索：'{metadata.get('title', '未知')}' 与主题 '{theme}' 不匹配（包含排除词）")
            continue

        if _has_theme_keyword_hit(retriever, theme, metadata, doc):
            valid_themes.append(theme)
        else:
            print(f"    ⚠️ 多主题检索：'{metadata.get('title', '未知')}' 与主题 '{theme}' 不匹配（未命中主题关键词）")

    return valid_themes


def _has_theme_keyword_hit(retriever, theme, metadata, doc):
    title = metadata.get("title", "") or ""
    source_file = metadata.get("source_file", "") or ""
    knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "") or ""
    haystack = f"{title} {source_file} {knowledge_tags} {doc or ''}"

    keywords = [theme]
    if retriever and getattr(retriever, "config_loader", None):
        keywords.extend(retriever.config_loader.get_theme_keywords(theme))

    deduped_keywords = []
    seen = set()
    for keyword in keywords:
        normalized = (keyword or "").strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            deduped_keywords.append(normalized)

    return any(keyword in haystack for keyword in deduped_keywords)
