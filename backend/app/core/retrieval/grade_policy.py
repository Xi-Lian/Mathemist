from typing import Any, Dict, Optional, Tuple


_HS_LEVELS = {"高一": 1, "高二": 2, "高三": 3}


def _normalize_grade_label(grade: str) -> str:
    text = (grade or "").strip()
    if not text:
        return ""
    if "高一" in text:
        return "高一"
    if "高二" in text:
        return "高二"
    if "高三" in text:
        return "高三"
    return text


def infer_level(grade: str, grade_level: Any = None) -> Optional[int]:
    if isinstance(grade_level, int):
        if grade_level >= 14:
            return 3
        if grade_level >= 13:
            return 2
        if grade_level >= 12:
            return 1
    return _HS_LEVELS.get(_normalize_grade_label(grade))


def strict_grade_match(resource_grade: Dict[str, Any], target_grade_info: Dict[str, Any]) -> Tuple[bool, str]:
    target_label = _normalize_grade_label(target_grade_info.get("grade", ""))
    resource_label = _normalize_grade_label(resource_grade.get("grade", ""))

    if not target_label:
        return True, "no_target_grade"
    if not resource_label:
        return True, "resource_grade_unknown"
    if target_label == resource_label:
        return True, "exact_grade_match"

    target_level = infer_level(target_label, target_grade_info.get("grade_level"))
    resource_level = infer_level(resource_label, resource_grade.get("grade_level"))
    if target_level is not None and resource_level is not None and abs(target_level - resource_level) <= 1:
        return True, "adjacent_grade_match"

    return False, "grade_mismatch"


def flexible_grade_score(resource_grade: Dict[str, Any], target_grade_info: Dict[str, Any]) -> Dict[str, Any]:
    passed, reason = strict_grade_match(resource_grade, target_grade_info)
    if passed:
        return {"pass": True, "reason": reason, "score_adjustment": 1.0 if reason == "exact_grade_match" else 0.85}

    target_level = infer_level(target_grade_info.get("grade", ""), target_grade_info.get("grade_level"))
    resource_level = infer_level(resource_grade.get("grade", ""), resource_grade.get("grade_level"))
    if target_level is not None and resource_level is not None:
        diff = abs(target_level - resource_level)
        score = max(0.35, 0.85 - 0.2 * diff)
        return {"pass": True, "reason": "distant_grade_deprioritized", "score_adjustment": score}

    return {"pass": True, "reason": "grade_unknown_deprioritized", "score_adjustment": 0.6}
