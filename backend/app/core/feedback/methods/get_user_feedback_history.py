from .._shared import *


class _GetUserFeedbackHistoryMixin:
    def get_user_feedback_history(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的反馈历史"""
        return self.feedback_data["user_feedback_history"].get(user_id, [])
