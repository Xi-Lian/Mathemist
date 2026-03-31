from .._shared import *
from ..balance_helpers.multi_theme import balance_multi_theme_resources
from ..balance_helpers.sorting import sort_resources_for_balance
from ..balance_helpers.threshold import apply_relevance_gap_filter


class _BalanceResourceDistributionMixin:
    def _balance_resource_distribution(self, resources: List[Dict[str, Any]], core_theme: str, query: str = "") -> List[Dict[str, Any]]:
        """
        平衡资源分布，确保每个主题都有合理数量的核心匹配资源
        """
        core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
        resources_sorted = sort_resources_for_balance(self, resources, core_theme, query)
        resources_sorted = apply_relevance_gap_filter(resources_sorted)

        if len(core_themes) > 1:
            return balance_multi_theme_resources(self, resources_sorted, core_themes)

        resources_sorted.sort(
            key=lambda x: (
                -x.get("is_core_match", False),
                -x.get("relevance", 0),
                -x.get("matched_theme_count", 0),
                -x.get("theme_boost", 0),
            )
        )
        return resources_sorted
