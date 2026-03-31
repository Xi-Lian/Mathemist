from .._shared import *


class _CheckFeedbackRateLimitMixin:
    def check_feedback_rate_limit(self, user_id: str) -> bool:
        """
        检查用户反馈频率限制
        
        Args:
            user_id: 用户ID
        
        Returns:
            是否允许反馈
        """
        rate_limit = self.feedback_data.get("config", {}).get("feedback_rate_limit", 10)
        current_time = datetime.now()
        one_hour_ago = current_time - timedelta(hours=1)
        
        user_feedbacks = self.feedback_data["user_feedback_history"].get(user_id, [])
        recent_feedbacks = [f for f in user_feedbacks if datetime.fromisoformat(f["timestamp"]) > one_hour_ago]
        
        return len(recent_feedbacks) < rate_limit
