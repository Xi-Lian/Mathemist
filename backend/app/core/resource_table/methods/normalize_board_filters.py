from .._shared import *


class _NormalizeBoardFiltersMixin:
    def _normalize_board_filters(self, boards: Optional[List[str]] = None) -> List[str]:
        """
        规范化板块过滤条件
        """
        if not boards:
            return []
        normalized: List[str] = []
        for board in boards:
            value = str(board).strip()
            if value and value not in normalized:
                normalized.append(value)
        return normalized
