"""
V90 主题匹配服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.calculate_precise_match import _CalculatePreciseMatchMixin
from .methods.match_single_theme_precise import _MatchSingleThemePreciseMixin
from .methods.determine_domain import _DetermineDomainMixin
from .methods.is_related_theme import _IsRelatedThemeMixin
from .methods.contains_exclusion_words import _ContainsExclusionWordsMixin
from .methods.calculate_domain_distance_factor import _CalculateDomainDistanceFactorMixin
from .methods.extract_lesson_theme import _ExtractLessonThemeMixin
from .methods.is_downward_recommendation import _IsDownwardRecommendationMixin
from .methods.calculate_weight_factor import _CalculateWeightFactorMixin
from .methods.calculate_overall_score import _CalculateOverallScoreMixin
from .methods.calculate_resource_quality import _CalculateResourceQualityMixin
from .methods.calculate_content_completeness import _CalculateContentCompletenessMixin
from .methods.calculate_teaching_value import _CalculateTeachingValueMixin
from .methods.calculate_comprehensiveness import _CalculateComprehensivenessMixin
from .methods.calculate_concept_hierarchy_factor import _CalculateConceptHierarchyFactorMixin
from .methods.calculate_exclusion_factor import _CalculateExclusionFactorMixin
from .methods.calculate_direction_factor import _CalculateDirectionFactorMixin
from .methods.calculate_dynamic_threshold import _CalculateDynamicThresholdMixin
from .methods.get_display_level import _GetDisplayLevelMixin
from .methods.extract_theme_keywords import _ExtractThemeKeywordsMixin
from .methods.get_theme_variants import _GetThemeVariantsMixin
from .methods.count_keyword_matches import _CountKeywordMatchesMixin
from .methods.parse_lesson_plan import _ParseLessonPlanMixin
from .methods.extract_query_themes import _ExtractQueryThemesMixin

class ThemeMatcherV90(_InitMixin, _CalculatePreciseMatchMixin, _MatchSingleThemePreciseMixin, _DetermineDomainMixin, _IsRelatedThemeMixin, _ContainsExclusionWordsMixin, _CalculateDomainDistanceFactorMixin, _ExtractLessonThemeMixin, _IsDownwardRecommendationMixin, _CalculateWeightFactorMixin, _CalculateOverallScoreMixin, _CalculateResourceQualityMixin, _CalculateContentCompletenessMixin, _CalculateTeachingValueMixin, _CalculateComprehensivenessMixin, _CalculateConceptHierarchyFactorMixin, _CalculateExclusionFactorMixin, _CalculateDirectionFactorMixin, _CalculateDynamicThresholdMixin, _GetDisplayLevelMixin, _ExtractThemeKeywordsMixin, _GetThemeVariantsMixin, _CountKeywordMatchesMixin, _ParseLessonPlanMixin, _ExtractQueryThemesMixin):
    """V9.2 主题匹配器"""


theme_matcher_v90 = None

def get_theme_matcher_v90() -> ThemeMatcherV90:
    """获取V9.0主题匹配器实例（单例模式）"""
    global theme_matcher_v90
    if theme_matcher_v90 is None:
        theme_matcher_v90 = ThemeMatcherV90()
    return theme_matcher_v90
