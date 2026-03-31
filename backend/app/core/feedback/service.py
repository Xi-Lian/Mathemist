"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.load_feedback import _LoadFeedbackMixin
from .methods.ensure_data_structure import _EnsureDataStructureMixin
from .methods.get_default_structure import _GetDefaultStructureMixin
from .methods.save_feedback import _SaveFeedbackMixin
from .methods.generate_feedback_id import _GenerateFeedbackIdMixin
from .methods.clean_expired_feedback import _CleanExpiredFeedbackMixin
from .methods.update_statistics import _UpdateStatisticsMixin
from .methods.check_feedback_rate_limit import _CheckFeedbackRateLimitMixin
from .methods.record_resource_feedback import _RecordResourceFeedbackMixin
from .methods.record_improvement_suggestion import _RecordImprovementSuggestionMixin
from .methods.update_feedback_status import _UpdateFeedbackStatusMixin
from .methods.get_resource_feedback import _GetResourceFeedbackMixin
from .methods.get_user_feedback_history import _GetUserFeedbackHistoryMixin
from .methods.get_feedback_processing_status import _GetFeedbackProcessingStatusMixin
from .methods.get_statistics import _GetStatisticsMixin
from .methods.get_improvement_suggestions import _GetImprovementSuggestionsMixin
from .methods.get_disliked_resources import _GetDislikedResourcesMixin
from .methods.get_feedback_trends import _GetFeedbackTrendsMixin
from .methods.get_resource_satisfaction import _GetResourceSatisfactionMixin
from .methods.export_feedback_data import _ExportFeedbackDataMixin

class UserFeedbackSystem(_InitMixin, _LoadFeedbackMixin, _EnsureDataStructureMixin, _GetDefaultStructureMixin, _SaveFeedbackMixin, _GenerateFeedbackIdMixin, _CleanExpiredFeedbackMixin, _UpdateStatisticsMixin, _CheckFeedbackRateLimitMixin, _RecordResourceFeedbackMixin, _RecordImprovementSuggestionMixin, _UpdateFeedbackStatusMixin, _GetResourceFeedbackMixin, _GetUserFeedbackHistoryMixin, _GetFeedbackProcessingStatusMixin, _GetStatisticsMixin, _GetImprovementSuggestionsMixin, _GetDislikedResourcesMixin, _GetFeedbackTrendsMixin, _GetResourceSatisfactionMixin, _ExportFeedbackDataMixin):
    """用户反馈系统"""


_feedback_system = None

def get_feedback_system() -> UserFeedbackSystem:
    """获取反馈系统实例"""
    global _feedback_system
    if _feedback_system is None:
        _feedback_system = UserFeedbackSystem()
    return _feedback_system
