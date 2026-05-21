from typing import Any, Dict, List, Optional, Set, Tuple


CATEGORY_PRIORS = {
    "theory_resources": 0.03,
    "lesson_plan_patterns": 0.06,
    "exercise_resources": 0.0,
    "visualization_examples": 0.02,
    "general_resources": 0.0,
    "courseware_resources": 0.05,
    "lesson_case_resources": 0.04,
    "ggb_resources": 0.04,
    "syllabus_resources": 0.03,
}
GENERAL_MATERIAL_HINTS = {"资料", "学习资料", "教学资源", "教学资料", "资源", "内容"}
EXPLICIT_EXERCISE_HINTS = {"习题", "题目", "练习题", "测试题", "选择题", "填空题", "解答题", "证明题"}
RESOURCE_TYPE_TO_CATEGORY = {
    "lesson_plan": "lesson_plan_patterns",
    "教案": "lesson_plan_patterns",
    "教学设计": "lesson_plan_patterns",
    "教学方案": "lesson_plan_patterns",
    "课件": "courseware_resources",
    "PPT": "courseware_resources",
    "演示文稿": "courseware_resources",
    "教学大纲": "syllabus_resources",
    "大纲": "syllabus_resources",
    "课程标准": "syllabus_resources",
    "exercise": "exercise_resources",
    "习题": "exercise_resources",
    "lesson_case": "lesson_case_resources",
    "课例": "lesson_case_resources",
    "ggb": "ggb_resources",
    "GGB": "ggb_resources",
    "theory": "theory_resources",
    "理论": "theory_resources",
}


def _collect_resources(classified: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    collected: List[Tuple[str, Dict[str, Any]]] = []
    for category, resources in classified.items():
        if not isinstance(resources, list):
            continue
        for resource in resources:
            if isinstance(resource, dict):
                collected.append((category, resource))
    return collected


def _contains_any(text: str, keywords: Set[str]) -> bool:
    return any(keyword in (text or "") for keyword in keywords)


def _requested_categories(resource_types: Optional[List[str]]) -> Set[str]:
    categories: Set[str] = set()
    for item in resource_types or []:
        mapped = RESOURCE_TYPE_TO_CATEGORY.get(item)
        if mapped:
            categories.add(mapped)
    return categories


def _build_query_profile(query: str = "", resource_types: Optional[List[str]] = None) -> Dict[str, Any]:
    requested = _requested_categories(resource_types)
    general_material = _contains_any(query, GENERAL_MATERIAL_HINTS) and not _contains_any(query, EXPLICIT_EXERCISE_HINTS)
    explicit_exercise = "exercise_resources" in requested or _contains_any(query, EXPLICIT_EXERCISE_HINTS)
    semantic_specific = bool(requested) and not explicit_exercise
    return {
        "requested_categories": requested,
        "general_material": general_material,
        "explicit_exercise": explicit_exercise,
        "semantic_specific": semantic_specific,
    }


def _policy_penalty(resource: Dict[str, Any]) -> float:
    penalty = 0.0
    if not resource.get("should_show", True):
        penalty += 0.4
    if resource.get("resource_quality", 1.0) < 0.3:
        penalty += 0.15
    if resource.get("content_completeness", 1.0) < 0.2:
        penalty += 0.1
    if resource.get("teaching_value", 1.0) < 0.1:
        penalty += 0.1
    return min(0.8, penalty)


def _looks_like_lesson_plan_attachment(resource: Dict[str, Any]) -> bool:
    title = f"{resource.get('title', '')} {resource.get('original_filename', '')} {resource.get('related_file', '')}".lower()
    source = str(resource.get("source", "") or "").lower()
    return any(marker in title for marker in ("课时作业", "作业", "导学案")) or source.endswith(".pdf")


def _semantic_score(resource: Dict[str, Any]) -> float:
    relevance = float(resource.get("relevance", 0.0) or 0.0)
    overall = float(resource.get("overall_score", relevance) or relevance)
    return max(0.0, min(1.0, 0.6 * relevance + 0.4 * overall))


def _recall_score(resource: Dict[str, Any]) -> float:
    metadata = resource.get("metadata", {}) if isinstance(resource.get("metadata"), dict) else {}
    distance = metadata.get("distance")
    if distance is None:
        return float(resource.get("base_relevance", resource.get("relevance", 0.0)) or 0.0)
    try:
        dist_val = float(distance)
        return max(0.0, min(1.0, 1.0 / (1.0 + dist_val)))
    except Exception:
        return float(resource.get("base_relevance", resource.get("relevance", 0.0)) or 0.0)


def _quality_score(resource: Dict[str, Any]) -> float:
    metrics = []
    for key in ("resource_quality", "content_completeness", "teaching_value", "comprehensiveness"):
        value = resource.get(key)
        if value is None:
            continue
        try:
            metrics.append(max(0.0, min(1.0, float(value))))
        except Exception:
            continue
    if not metrics:
        return 0.5
    return sum(metrics) / len(metrics)


def _exercise_content_richness_boost(category: str, resource: Dict[str, Any], profile: Dict[str, Any]) -> float:
    if category != "exercise_resources":
        return 0.0

    boost = 0.0
    if resource.get("has_question_image"):
        boost += 0.12
    if resource.get("has_answer_image"):
        boost += 0.06
    if resource.get("is_image_exercise"):
        boost += 0.04

    # 显式习题请求下，优先把内容更完整、可直接渲染的题目排到前面。
    if boost > 0 and profile.get("explicit_exercise"):
        boost += 0.04

    return min(0.20, boost)


def _request_alignment_boost(category: str, profile: Dict[str, Any]) -> float:
    requested = profile["requested_categories"]
    if requested:
        if category in requested:
            return 0.18
        if profile["semantic_specific"]:
            return -0.08

    if profile["explicit_exercise"]:
        return 0.14 if category == "exercise_resources" else -0.04

    if profile["general_material"]:
        if category in {"theory_resources", "lesson_plan_patterns", "courseware_resources", "syllabus_resources"}:
            return 0.08
        if category == "exercise_resources":
            return -0.12

    return 0.0


def _score_resource(category: str, resource: Dict[str, Any], profile: Dict[str, Any]) -> float:
    recall = _recall_score(resource)
    semantic = _semantic_score(resource)
    quality = _quality_score(resource)
    penalty = _policy_penalty(resource)
    prior = CATEGORY_PRIORS.get(category, 0.0)
    request_boost = _request_alignment_boost(category, profile)
    richness_boost = _exercise_content_richness_boost(category, resource, profile)
    explicit_exercise_penalty = 0.0
    if profile["explicit_exercise"] and category != "exercise_resources":
        explicit_exercise_penalty += 0.18
        if category == "lesson_plan_patterns" and _looks_like_lesson_plan_attachment(resource):
            explicit_exercise_penalty += 0.22
    score = 0.22 * recall + 0.43 * semantic + 0.20 * quality + prior + request_boost + richness_boost - penalty
    score -= explicit_exercise_penalty
    resource["final_rank_score"] = max(0.0, min(1.0, score))
    resource["ranking_debug"] = {
        "recall_score": recall,
        "semantic_score": semantic,
        "quality_score": quality,
        "policy_penalty": penalty,
        "category_prior": prior,
        "request_alignment_boost": request_boost,
        "exercise_content_richness_boost": richness_boost,
        "explicit_exercise_penalty": explicit_exercise_penalty,
    }
    return resource["final_rank_score"]


def _build_category_caps(profile: Dict[str, Any], quantity_limit: Optional[int], candidate_count: int) -> Dict[str, int]:
    if not quantity_limit or quantity_limit <= 0:
        return {}

    default_cap = max(2, quantity_limit)
    caps: Dict[str, int] = {}
    if profile["requested_categories"]:
        # 当用户明确指定资源类型时，只返回指定的类型，其他类型的上限设为0
        requested_categories = profile["requested_categories"]
        for category in CATEGORY_PRIORS:
            if category in requested_categories:
                caps[category] = quantity_limit
            else:
                caps[category] = 0
        return caps

    if profile["explicit_exercise"]:
        caps["exercise_resources"] = quantity_limit
        for category in CATEGORY_PRIORS:
            if category != "exercise_resources":
                caps[category] = 0
        return caps

    if profile["general_material"]:
        caps["exercise_resources"] = max(2, quantity_limit // 4)
        caps["theory_resources"] = quantity_limit
        caps["lesson_plan_patterns"] = quantity_limit
        caps["courseware_resources"] = quantity_limit
        caps["syllabus_resources"] = max(2, quantity_limit // 2)
        return caps

    return {category: default_cap for category in CATEGORY_PRIORS}


def _apply_diversity_selection(
    scored: List[Tuple[str, Dict[str, Any], float]],
    profile: Dict[str, Any],
    quantity_limit: Optional[int],
) -> List[Tuple[str, Dict[str, Any], float]]:
    if not quantity_limit or quantity_limit <= 0:
        return scored

    caps = _build_category_caps(profile, quantity_limit, len(scored))
    selected: List[Tuple[str, Dict[str, Any], float]] = []
    deferred: List[Tuple[str, Dict[str, Any], float]] = []
    counts: Dict[str, int] = {}

    for item in scored:
        category = item[0]
        cap = caps.get(category, quantity_limit)
        if cap <= 0:
            continue
        if counts.get(category, 0) < cap:
            selected.append(item)
            counts[category] = counts.get(category, 0) + 1
        else:
            deferred.append(item)
        if len(selected) >= quantity_limit:
            return selected

    if len(selected) < quantity_limit:
        remaining = quantity_limit - len(selected)
        selected.extend(deferred[:remaining])
    return selected


def apply_unified_ranking(
    classified: Dict[str, Any],
    quantity_limit: int = None,
    query: str = "",
    resource_types: Optional[List[str]] = None,
) -> Dict[str, Any]:
    collected = _collect_resources(classified)
    if not collected:
        classified["_ranking"] = {
            "strategy": "single_ranker_v1",
            "candidate_count": 0,
        }
        return classified

    profile = _build_query_profile(query, resource_types)
    scored: List[Tuple[str, Dict[str, Any], float]] = []
    for category, resource in collected:
        score = _score_resource(category, resource, profile)
        scored.append((category, resource, score))

    scored.sort(key=lambda item: item[2], reverse=True)
    scored = _apply_diversity_selection(scored, profile, quantity_limit)

    rebuilt: Dict[str, Any] = {}
    for key, value in classified.items():
        rebuilt[key] = [] if isinstance(value, list) else value

    for category, resource, _ in scored:
        rebuilt.setdefault(category, [])
        rebuilt[category].append(resource)

    total_visible = 0
    for key, value in rebuilt.items():
        if isinstance(value, list) and not key.startswith("_"):
            total_visible += len(value)

    rebuilt["_ranking"] = {
        "strategy": "single_ranker_v1",
        "candidate_count": len(collected),
        "selected_count": len(scored),
        "quantity_limit": quantity_limit,
        "total_visible": total_visible,
        "query_profile": {
            "requested_categories": sorted(profile["requested_categories"]),
            "general_material": profile["general_material"],
            "explicit_exercise": profile["explicit_exercise"],
            "semantic_specific": profile["semantic_specific"],
        },
    }
    return rebuilt
