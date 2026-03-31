from .._shared import *


class _SaveHistoryMixin:
    def _save_history(self, history: List[Dict[str, Any]]):
        """保存备课历史"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
