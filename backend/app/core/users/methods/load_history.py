from .._shared import *


class _LoadHistoryMixin:
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载备课历史"""
        with open(self.history_file, 'r', encoding='utf-8') as f:
            return json.load(f)
