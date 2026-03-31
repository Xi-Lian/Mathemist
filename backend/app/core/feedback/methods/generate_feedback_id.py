from .._shared import *


class _GenerateFeedbackIdMixin:
    def _generate_feedback_id(self) -> str:
        """生成反馈ID"""
        return f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
