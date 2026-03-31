from .._shared import *


class _ClearContextMixin:
    def clear_context(self) -> None:
        """
        清除上下文历史
        """
        self.context_history = []
