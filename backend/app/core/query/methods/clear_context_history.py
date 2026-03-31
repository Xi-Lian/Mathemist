from .._shared import *


class _ClearContextHistoryMixin:
    def clear_context_history(self) -> None:
        """
        V33.0改进：清除上下文历史
        """
        self.context_history = []
