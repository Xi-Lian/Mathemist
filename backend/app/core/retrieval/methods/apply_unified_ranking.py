from .._shared import *
from ..ranking_helpers import apply_unified_ranking


class _ApplyUnifiedRankingMixin:
    def _apply_unified_ranking(
        self,
        classified_resources: Dict[str, Any],
        quantity_limit: Optional[int] = None,
        query: str = "",
        resource_types: List[str] = None,
    ) -> Dict[str, Any]:
        try:
            return apply_unified_ranking(
                classified_resources,
                quantity_limit,
                query=query,
                resource_types=resource_types,
            )
        except Exception as e:
            print(f"⚠️ 统一排序中心失败，保留原结果: {e}")
            classified_resources["_ranking"] = {
                "strategy": "single_ranker_v1",
                "error": str(e),
            }
            return classified_resources
