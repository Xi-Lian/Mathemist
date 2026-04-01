from .._shared import *

RESOURCE_RELEVANCE_POLICY = {
    "lesson_plan": {"min_relevance": None, "min_overall_score": 0.20},
    "courseware": {"min_relevance": 0.10, "min_overall_score": None},
    "exercise": {"min_relevance": 0.25, "min_overall_score": None},
    "ggb": {"min_relevance": 0.15, "min_overall_score": None},
    "lesson_case": {"min_relevance": 0.20, "min_overall_score": None},
    "syllabus": {"min_relevance": 0.20, "min_overall_score": None},
    "default": {"min_relevance": 0.30, "min_overall_score": None},
}


def update_resource_with_match(resource, match_result):
    resource["matched_themes"] = match_result["matched_themes"]
    resource["matched_theme_count"] = len(match_result["matched_themes"])
    resource["core_theme"] = match_result["core_theme_match"]
    resource["related_themes"] = match_result["related_themes"]
    resource["mentioned_themes"] = match_result["mentioned_themes"]
    resource["is_core_match"] = match_result["is_core_match"]
    resource["match_level"] = match_result["match_level"]
    resource["domain"] = match_result["domain"]
    resource["match_explanation"] = match_result["explanation"]
    resource["should_show"] = match_result["should_show"]
    resource["overall_score"] = match_result["overall_score"]
    resource["resource_quality"] = match_result["resource_quality"] if match_result["resource_quality"] is not None else 0.0
    resource["content_completeness"] = (
        match_result["content_completeness"] if match_result["content_completeness"] is not None else 0.0
    )
    resource["teaching_value"] = match_result["teaching_value"] if match_result["teaching_value"] is not None else 0.0
    resource["comprehensiveness"] = match_result["comprehensiveness"] if match_result["comprehensiveness"] is not None else 0.0
    resource["concept_hierarchy_factor"] = match_result["concept_hierarchy_factor"]
    resource["theme_match"] = resource["matched_theme_count"] > 0
    resource["theme_boost"] = match_result["relevance_score"]


def apply_relevance_thresholds(resource, resource_type, resource_types):
    final_relevance = resource["match_result"]["relevance_score"]
    is_core_match = resource["is_core_match"]
    should_show = resource["should_show"]
    overall_score = resource["overall_score"]
    policy = RESOURCE_RELEVANCE_POLICY.get(resource_type, RESOURCE_RELEVANCE_POLICY["default"])
    min_relevance = policy["min_relevance"]
    min_overall_score = policy["min_overall_score"]

    if min_overall_score is not None and overall_score > 0:
        if overall_score >= min_overall_score:
            should_show = True
            final_relevance = max(final_relevance, overall_score)
        else:
            should_show = False
            final_relevance = 0.0
    elif min_relevance is not None and final_relevance < min_relevance and not is_core_match:
        final_relevance = 0.0
        should_show = False

    print(
        f"   🔍 V92.0最终相关性检查 - resource_type: {resource_type}, "
        f"final_relevance: {final_relevance:.4f}, is_core_match: {is_core_match}, should_show: {should_show}"
    )

    resource["debug_info"] = {
        "base_relevance": resource["base_relevance"],
        "avg_theme_score": resource["match_result"]["relevance_score"],
        "matched_themes": resource["matched_themes"],
        "core_theme": resource["core_theme"],
        "related_themes": resource["related_themes"],
        "mentioned_themes": resource["mentioned_themes"],
        "is_core_match": resource["is_core_match"],
        "match_level": resource["match_level"],
        "domain": resource["domain"],
        "explanation": resource["match_explanation"],
        "should_show": should_show,
        "formula": f"V9.0统一匹配: {final_relevance:.2f}",
    }

    resource["relevance"] = max(0.0, min(1.0, final_relevance))
    resource["should_show"] = should_show
    _apply_resource_type_boost(resource, resource_type, resource_types)


def _apply_resource_type_boost(resource, resource_type, resource_types):
    if not resource_types or any(rt in ["资料", "资源"] for rt in resource_types):
        return

    type_matched = False
    for user_type in resource_types:
        mapped_db_type = get_db_type(user_type)
        if mapped_db_type and resource_type == mapped_db_type:
            type_matched = True
            break
        if not mapped_db_type and user_type.lower() in resource_type.lower():
            type_matched = True
            break

    if type_matched:
        resource["relevance"] = min(1.0, resource["relevance"] + 0.05)
        resource["type_match"] = True
        resource["type_boost"] = 0.05


def run_resource_processors(retriever, resource, metadata, resource_type):
    if resource_type == "exercise":
        retriever._process_exercise_resource(resource, metadata)
    elif resource_type == "ggb":
        retriever._process_ggb_resource(resource, metadata)
    elif resource_type == "syllabus":
        retriever._process_syllabus_resource(resource, metadata)
    elif resource_type == "lesson_plan":
        retriever._process_lesson_plan_resource(resource, metadata)
    elif resource_type == "courseware":
        retriever._process_courseware_resource(resource, metadata)
    elif resource_type == "lesson_case":
        retriever._process_lesson_case_resource(resource, metadata)


def apply_quality_controls(retriever, resource, resource_type):
    if resource.get("resource_quality", 0) < 0.3:
        resource["relevance"] *= 0.8
    if resource.get("content_completeness", 0) < 0.2:
        resource["relevance"] *= 0.7
    if resource.get("teaching_value", 0) < 0.1:
        resource["relevance"] *= 0.6
    resource["relevance"] = max(0.0, resource["relevance"])
    print(f"   🔍 V90.2质量控制 - resource_type: {resource_type}, should_show: {resource['should_show']}, relevance: {resource['relevance']:.4f}")
    resource["overall_score"] = retriever._calculate_overall_score(resource, resource["is_core_match"])
    print(f"   🔍 V90.2返回资源 - should_show: {resource['should_show']}, resource['should_show']: {resource.get('should_show', 'not set')}")
