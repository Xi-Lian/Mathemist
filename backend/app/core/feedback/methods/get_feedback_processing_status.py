from .._shared import *


class _GetFeedbackProcessingStatusMixin:
    def get_feedback_processing_status(self, feedback_id: str) -> Dict[str, Any]:
        """获取反馈处理状态"""
        return self.feedback_data["feedback_processing"].get(feedback_id, {})
