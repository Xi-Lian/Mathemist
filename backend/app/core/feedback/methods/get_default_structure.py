from .._shared import *


class _GetDefaultStructureMixin:
    def _get_default_structure(self) -> Dict[str, Any]:
        """获取默认数据结构"""
        return {
            "resource_feedback": {},  # 资源反馈: {resource_id: [{...}]}
            "improvement_suggestions": [],  # 改进建议列表
            "user_feedback_history": {},  # 用户反馈历史: {user_id: [{...}]}
            "feedback_processing": {},  # 反馈处理状态: {feedback_id: {...}}
            "statistics": {
                "total_likes": 0,
                "total_dislikes": 0,
                "total_feedback": 0,
                "total_suggestions": 0,
                "feedback_by_theme": {},
                "feedback_by_type": {},
                "feedback_by_date": {},
                "satisfaction_score": 0.0
            },
            "config": {
                "feedback_rate_limit": 10,  # 每小时最大反馈次数
                "feedback_expiry_days": 365  # 反馈数据保留天数
            }
        }
