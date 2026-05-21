"""
教案生成服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.load_lesson_plan_common_characteristics import _LoadLessonPlanCommonCharacteristicsMixin
from .methods.load_theory_cards import _LoadTheoryCardsMixin
from .methods.parse_theory_cards import _ParseTheoryCardsMixin
from .methods.parse_teaching_inspiration_elements import _ParseTeachingInspirationElementsMixin
from .methods.extract_applicable_methods import _ExtractApplicableMethodsMixin
from .methods.extract_applicable_content import _ExtractApplicableContentMixin
from .methods.extract_theory_elements import _ExtractTheoryElementsMixin
from .methods.enhance_theory_card_parsing import _EnhanceTheoryCardParsingMixin
from .methods.generate_deep_theory_reference import _GenerateDeepTheoryReferenceMixin
from .methods.generate_application_case import _GenerateApplicationCaseMixin
from .methods.validate_theory_references import _ValidateTheoryReferencesMixin
from .methods.get_recommended_theories import _GetRecommendedTheoriesMixin
from .methods.get_dynamic_recommended_theories import _GetDynamicRecommendedTheoriesMixin
from .methods.validate_theory_method_match import _ValidateTheoryMethodMatchMixin
from .methods.monitor_theory_frequency import _MonitorTheoryFrequencyMixin
from .methods.check_theory_diversity import _CheckTheoryDiversityMixin
from .methods.check_theory_consistency import _CheckTheoryConsistencyMixin
from .methods.analyze_student_level import _AnalyzeStudentLevelMixin
from .methods.analyze_class_type import _AnalyzeClassTypeMixin
from .methods.analyze_special_requirements import _AnalyzeSpecialRequirementsMixin
from .methods.analyze_theory_preferences import _AnalyzeTheoryPreferencesMixin
from .methods.format_all_theory_references import _FormatAllTheoryReferencesMixin
from .methods.enhance_theory_depth import _EnhanceTheoryDepthMixin
from .methods.is_theory_suitable_for_method import _IsTheorySuitableForMethodMixin
from .methods.evaluate_theory_quality import _EvaluateTheoryQualityMixin
from .methods.update_theory_summary import _UpdateTheorySummaryMixin
from .methods.generate import _GenerateMixin
from .methods.analyze_teaching_method import _AnalyzeTeachingMethodMixin
from .methods.analyze_content_type import _AnalyzeContentTypeMixin
from .methods.format_theory_resources import _FormatTheoryResourcesMixin
from .methods.extract_section import _ExtractSectionMixin
from .methods.format_lesson_plan_patterns import _FormatLessonPlanPatternsMixin
from .methods.format_excellent_case_resources import _FormatExcellentCaseResourcesMixin
from .methods.get_error_response import _GetErrorResponseMixin
from .methods.check_lesson_plan_completeness import _CheckLessonPlanCompletenessMixin
from .methods.create_prompt_template import _CreatePromptTemplateMixin

class LessonPlanGenerator(_InitMixin, _LoadLessonPlanCommonCharacteristicsMixin, _LoadTheoryCardsMixin, _ParseTheoryCardsMixin, _ParseTeachingInspirationElementsMixin, _ExtractApplicableMethodsMixin, _ExtractApplicableContentMixin, _ExtractTheoryElementsMixin, _EnhanceTheoryCardParsingMixin, _GenerateDeepTheoryReferenceMixin, _GenerateApplicationCaseMixin, _ValidateTheoryReferencesMixin, _GetRecommendedTheoriesMixin, _GetDynamicRecommendedTheoriesMixin, _ValidateTheoryMethodMatchMixin, _MonitorTheoryFrequencyMixin, _CheckTheoryDiversityMixin, _CheckTheoryConsistencyMixin, _AnalyzeStudentLevelMixin, _AnalyzeClassTypeMixin, _AnalyzeSpecialRequirementsMixin, _AnalyzeTheoryPreferencesMixin, _FormatAllTheoryReferencesMixin, _EnhanceTheoryDepthMixin, _IsTheorySuitableForMethodMixin, _EvaluateTheoryQualityMixin, _UpdateTheorySummaryMixin, _GenerateMixin, _AnalyzeTeachingMethodMixin, _AnalyzeContentTypeMixin, _FormatTheoryResourcesMixin, _ExtractSectionMixin, _FormatLessonPlanPatternsMixin, _FormatExcellentCaseResourcesMixin, _GetErrorResponseMixin, _CheckLessonPlanCompletenessMixin, _CreatePromptTemplateMixin):
    """教案生成器"""

def lesson_plan_generation_node(state) -> Dict[str, Any]:
    """
    教案生成节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含教案的更新状态
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 提取检索到的资源
    lesson_plan_patterns = []
    
    if isinstance(state, dict):
        retrieved_resources = state.get('retrieved_resources', {})
        lesson_plan_patterns = retrieved_resources.get('lesson_plan_patterns', [])
    
    # 从向量数据库获取理论资源
    theory_resources = []
    try:
        from ..resource_retriever import ResourceRetriever
        retriever = ResourceRetriever()
        theory_resources = retriever.get_theory_resources()
        print(f"📚 从向量数据库获取理论资源: {len(theory_resources)}条")
    except Exception as e:
        print(f"⚠️  获取理论资源失败: {str(e)}")
    
    # 生成教案
    generator = LessonPlanGenerator()
    lesson_plan = generator.generate(user_input, theory_resources, lesson_plan_patterns)
    
    return {
        "lesson_plan": lesson_plan,
        "current_step": "lesson_plan_generation",
        "error": None
    }
