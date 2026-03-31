from .._shared import *


class _GetResourceSatisfactionMixin:
    def get_resource_satisfaction(self, resource_id: str) -> Dict[str, Any]:
        """获取资源满意度"""
        feedbacks = self.feedback_data["resource_feedback"].get(resource_id, [])
        if not feedbacks:
            return {
                "resource_id": resource_id,
                "total_feedback": 0,
                "likes": 0,
                "dislikes": 0,
                "satisfaction_score": 0.0,
                "recent_feedback": []
            }
        
        total_feedback = len(feedbacks)
        likes = sum(1 for f in feedbacks if f["is_like"])
        dislikes = total_feedback - likes
        satisfaction_score = round(likes / total_feedback, 2) if total_feedback > 0 else 0.0
        
        # 获取最近的5条反馈
        recent_feedback = sorted(feedbacks, key=lambda x: x["timestamp"], reverse=True)[:5]
        
        return {
            "resource_id": resource_id,
            "total_feedback": total_feedback,
            "likes": likes,
            "dislikes": dislikes,
            "satisfaction_score": satisfaction_score,
            "recent_feedback": recent_feedback
        }
