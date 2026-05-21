from .._shared import *
from .evaluation_parts.common import build_no_core_theme_result
from .evaluation_parts.exercise import evaluate_exercise_match
from .evaluation_parts.multi_theme import evaluate_multi_theme_match
from .evaluation_parts.non_exercise import evaluate_non_exercise_match


def evaluate_resource_match(
    retriever,
    doc,
    metadata,
    base_relevance,
    resource_type,
    core_theme,
    query,
    question_type,
):
    multi_theme_info = metadata.get("_matched_themes", [])
    if multi_theme_info:
        return evaluate_multi_theme_match(retriever, doc, metadata, base_relevance, core_theme, multi_theme_info)
    if core_theme:
        if resource_type == "exercise":
            return evaluate_exercise_match(retriever, doc, metadata, base_relevance, core_theme, query, question_type, multi_theme_info)
        return evaluate_non_exercise_match(retriever, doc, metadata, base_relevance, resource_type, core_theme, query)
    return build_no_core_theme_result(base_relevance, resource_type)
