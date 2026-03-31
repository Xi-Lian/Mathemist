"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.preprocess import _PreprocessMixin
from .methods.classify_query_type import _ClassifyQueryTypeMixin
from .methods.calculate_query_clarity import _CalculateQueryClarityMixin
from .methods.identify_instruction_type import _IdentifyInstructionTypeMixin
from .methods.extract_complete_theme import _ExtractCompleteThemeMixin
from .methods.extract_topic_after_instruction import _ExtractTopicAfterInstructionMixin
from .methods.extract_intent import _ExtractIntentMixin
from .methods.clean_query import _CleanQueryMixin
from .methods.extract_latex import _ExtractLatexMixin
from .methods.clean_latex_expression import _CleanLatexExpressionMixin
from .methods.extract_keywords import _ExtractKeywordsMixin
from .methods.extract_core_concepts import _ExtractCoreConceptsMixin
from .methods.generate_search_versions import _GenerateSearchVersionsMixin
from .methods.expand_query_with_synonyms import _ExpandQueryWithSynonymsMixin
from .methods.enhance_with_context import _EnhanceWithContextMixin
from .methods.update_context_history import _UpdateContextHistoryMixin
from .methods.clear_context_history import _ClearContextHistoryMixin

class QueryPreprocessor(_InitMixin, _PreprocessMixin, _ClassifyQueryTypeMixin, _CalculateQueryClarityMixin, _IdentifyInstructionTypeMixin, _ExtractCompleteThemeMixin, _ExtractTopicAfterInstructionMixin, _ExtractIntentMixin, _CleanQueryMixin, _ExtractLatexMixin, _CleanLatexExpressionMixin, _ExtractKeywordsMixin, _ExtractCoreConceptsMixin, _GenerateSearchVersionsMixin, _ExpandQueryWithSynonymsMixin, _EnhanceWithContextMixin, _UpdateContextHistoryMixin, _ClearContextHistoryMixin):
    """查询预处理器"""


_query_preprocessor = None

def get_query_preprocessor() -> QueryPreprocessor:
    """
    获取查询预处理器单例
    """
    global _query_preprocessor
    if _query_preprocessor is None:
        _query_preprocessor = QueryPreprocessor()
    return _query_preprocessor
