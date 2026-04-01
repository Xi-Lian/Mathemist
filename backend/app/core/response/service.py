"""
响应构建服务实现。
"""

import uuid

from ._shared import *
from .methods.init import _InitMixin
from .methods.build import _BuildMixin
from .methods.build_multi_intent_response import _BuildMultiIntentResponseMixin
from .methods.build_lesson_plan_response import _BuildLessonPlanResponseMixin
from .methods.build_visualization_response import _BuildVisualizationResponseMixin
from .methods.build_search_response import _BuildSearchResponseMixin
from .methods.format_resources import _FormatResourcesMixin
from .methods.classify_resource_domain import _ClassifyResourceDomainMixin
from .methods.get_priority_domains import _GetPriorityDomainsMixin
from .methods.is_parallel_query import _IsParallelQueryMixin
from .methods.calculate_query_specificity import _CalculateQuerySpecificityMixin
from .methods.generate_dynamic_categories import _GenerateDynamicCategoriesMixin
from .methods.generate_coarse_grained_categories import _GenerateCoarseGrainedCategoriesMixin
from .methods.generate_medium_grained_categories import _GenerateMediumGrainedCategoriesMixin
from .methods.generate_fine_grained_categories import _GenerateFineGrainedCategoriesMixin
from .methods.record_user_feedback import _RecordUserFeedbackMixin
from .methods.analyze_feedback_data import _AnalyzeFeedbackDataMixin
from .methods.optimize_ranking_with_feedback import _OptimizeRankingWithFeedbackMixin
from .methods.calculate_multi_dimension_score import _CalculateMultiDimensionScoreMixin
from .methods.calculate_unified_score import _CalculateUnifiedScoreMixin
from .methods.sort_resources_globally import _SortResourcesGloballyMixin
from .methods.format_resources_by_theme import _FormatResourcesByThemeMixin
from .methods.format_resources_by_domain import _FormatResourcesByDomainMixin
from .methods.format_resource_category import _FormatResourceCategoryMixin
from .methods.append_resource_info import _AppendResourceInfoMixin
from .methods.filter_by_relevance import _FilterByRelevanceMixin
from .methods.process_resource_content import _ProcessResourceContentMixin
from .methods.get_error_response import _GetErrorResponseMixin
from .methods.check_timeout import _CheckTimeoutMixin
from .methods.get_timeout_response import _GetTimeoutResponseMixin
from .methods.get_fallback_response import _GetFallbackResponseMixin
from .methods.get_state_value import _GetStateValueMixin

class ResponseBuilder(_InitMixin, _BuildMixin, _BuildMultiIntentResponseMixin, _BuildLessonPlanResponseMixin, _BuildVisualizationResponseMixin, _BuildSearchResponseMixin, _FormatResourcesMixin, _ClassifyResourceDomainMixin, _GetPriorityDomainsMixin, _IsParallelQueryMixin, _CalculateQuerySpecificityMixin, _GenerateDynamicCategoriesMixin, _GenerateCoarseGrainedCategoriesMixin, _GenerateMediumGrainedCategoriesMixin, _GenerateFineGrainedCategoriesMixin, _RecordUserFeedbackMixin, _AnalyzeFeedbackDataMixin, _OptimizeRankingWithFeedbackMixin, _CalculateMultiDimensionScoreMixin, _CalculateUnifiedScoreMixin, _SortResourcesGloballyMixin, _FormatResourcesByThemeMixin, _FormatResourcesByDomainMixin, _FormatResourceCategoryMixin, _AppendResourceInfoMixin, _FilterByRelevanceMixin, _ProcessResourceContentMixin, _GetErrorResponseMixin, _CheckTimeoutMixin, _GetTimeoutResponseMixin, _GetFallbackResponseMixin, _GetStateValueMixin):
    """响应构建器"""


def _get_existing_messages(state) -> list[dict]:
    if isinstance(state, dict):
        messages = state.get("messages", [])
    else:
        messages = getattr(state, "messages", [])
    if not isinstance(messages, list):
        return []
    return [message for message in messages if isinstance(message, dict)]


def response_formatting_node(state) -> Dict[str, Any]:
    """
    响应格式化节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含响应的更新状态
    """
    # 构建响应
    builder = ResponseBuilder()
    response = builder.build(state)

    assistant_message = {
        "id": f"msg_{uuid.uuid4().hex}",
        "type": "ai",
        "content": response,
    }
    updated_messages = [*_get_existing_messages(state), assistant_message]
    
    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "message": assistant_message,
        "messages": updated_messages,
    }
