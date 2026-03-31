from .._shared import *


class _GetResourceFeedbackMixin:
    def get_resource_feedback(self, resource_id: str) -> List[Dict[str, Any]]:
        """获取资源的所有反馈"""
        return self.feedback_data["resource_feedback"].get(resource_id, [])
