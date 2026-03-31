from .._shared import *


class _GetDislikedResourcesMixin:
    def get_disliked_resources(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取被点踩最多的资源"""
        disliked = []
        for resource_id, feedbacks in self.feedback_data["resource_feedback"].items():
            dislike_count = sum(1 for f in feedbacks if not f["is_like"])
            if dislike_count > 0:
                disliked.append({
                    "resource_id": resource_id,
                    "dislike_count": dislike_count,
                    "feedbacks": feedbacks
                })
        disliked.sort(key=lambda x: x["dislike_count"], reverse=True)
        return disliked[:limit]
