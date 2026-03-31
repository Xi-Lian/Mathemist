from .._shared import *


class _GetStatisticsMixin:
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.feedback_data["statistics"]
