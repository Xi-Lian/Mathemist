from .._shared import *


class _CleanExpiredFeedbackMixin:
    def _clean_expired_feedback(self):
        """清理过期的反馈数据"""
        expiry_days = self.feedback_data.get("config", {}).get("feedback_expiry_days", 365)
        cutoff_date = datetime.now() - timedelta(days=expiry_days)
        
        # 清理资源反馈
        for resource_id, feedbacks in list(self.feedback_data["resource_feedback"].items()):
            filtered_feedbacks = []
            for feedback in feedbacks:
                feedback_date = datetime.fromisoformat(feedback["timestamp"])
                if feedback_date > cutoff_date:
                    filtered_feedbacks.append(feedback)
            if filtered_feedbacks:
                self.feedback_data["resource_feedback"][resource_id] = filtered_feedbacks
            else:
                del self.feedback_data["resource_feedback"][resource_id]
        
        # 清理改进建议
        filtered_suggestions = []
        for suggestion in self.feedback_data["improvement_suggestions"]:
            suggestion_date = datetime.fromisoformat(suggestion["timestamp"])
            if suggestion_date > cutoff_date:
                filtered_suggestions.append(suggestion)
        self.feedback_data["improvement_suggestions"] = filtered_suggestions
        
        # 清理用户反馈历史
        for user_id, feedbacks in list(self.feedback_data["user_feedback_history"].items()):
            filtered_feedbacks = []
            for feedback in feedbacks:
                feedback_date = datetime.fromisoformat(feedback["timestamp"])
                if feedback_date > cutoff_date:
                    filtered_feedbacks.append(feedback)
            if filtered_feedbacks:
                self.feedback_data["user_feedback_history"][user_id] = filtered_feedbacks
            else:
                del self.feedback_data["user_feedback_history"][user_id]
