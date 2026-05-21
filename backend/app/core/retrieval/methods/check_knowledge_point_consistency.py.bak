from .._shared import *
from ..consistency_helpers.context import (
    build_consistency_context,
    extract_specific_knowledge_points,
    should_skip_consistency_check,
)
from ..consistency_helpers.matching import contains_conflicting_theme, has_knowledge_match
from ..consistency_helpers.paths import has_path_conflict


class _CheckKnowledgePointConsistencyMixin:
    def _check_knowledge_point_consistency(
        self,
        metadata: Dict[str, Any],
        core_theme: str,
        doc: str = "",
        query: str = "",
        relevance: float = 0.0,
    ) -> bool:
        """
        V15.0: 检查习题的知识点是否与查询要求一致
        """
        if not core_theme:
            return True

        context = build_consistency_context(metadata, core_theme, doc, query, relevance)
        themes = context["themes"]
        if should_skip_consistency_check(core_theme, relevance, themes):
            return True

        specific_knowledge_points = extract_specific_knowledge_points(themes)
        if has_path_conflict(self, metadata, specific_knowledge_points, context["source_file"], relevance):
            return False

        has_match = has_knowledge_match(
            self,
            specific_knowledge_points,
            context["knowledge_tags"],
            context["source_file"],
            context["title"],
            context["question_content"],
            context["question_file"],
        )
        if has_match:
            return True

        if contains_conflicting_theme(self, specific_knowledge_points, context["all_info"], relevance):
            return False

        return relevance > 0.6
