"""
资源检索服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.detect_query_intents import _DetectQueryIntentsMixin
from .methods.enhance_query_dynamically import _EnhanceQueryDynamicallyMixin
from .methods.basic_query_enhancement import _BasicQueryEnhancementMixin
from .methods.adjust_retrieval_count import _AdjustRetrievalCountMixin
from .methods.retrieve import _RetrieveMixin
from .methods.apply_ai_rerank import _ApplyAiRerankMixin
from .methods.apply_unified_ranking import _ApplyUnifiedRankingMixin
from .methods.check_vector_db_exists import _CheckVectorDbExistsMixin
from .methods.generate_query_embedding import _GenerateQueryEmbeddingMixin
from .methods.merge_multi_theme_results import _MergeMultiThemeResultsMixin
from .methods.check_theme_relevance_with_llm import _CheckThemeRelevanceWithLlmMixin
from .methods.check_knowledge_point_consistency import _CheckKnowledgePointConsistencyMixin
from .methods.classify_results import _ClassifyResultsMixin
from .methods.dynamic_classify_resource import _DynamicClassifyResourceMixin
from .methods.apply_grade_filter import _ApplyGradeFilterMixin
from .methods.apply_topic_exclusion import _ApplyTopicExclusionMixin
from .methods.apply_quantity_limit import _ApplyQuantityLimitMixin
from .methods.get_metadata import _GetMetadataMixin
from .methods.get_distance import _GetDistanceMixin
from .methods.create_resource import _CreateResourceMixin
from .methods.calculate_overall_score import _CalculateOverallScoreMixin
from .methods.process_exercise_resource import _ProcessExerciseResourceMixin
from .methods.process_ggb_resource import _ProcessGgbResourceMixin
from .methods.process_syllabus_resource import _ProcessSyllabusResourceMixin
from .methods.process_lesson_plan_resource import _ProcessLessonPlanResourceMixin
from .methods.process_courseware_resource import _ProcessCoursewareResourceMixin
from .methods.process_lesson_case_resource import _ProcessLessonCaseResourceMixin
from .methods.extract_topic_from_filename import _ExtractTopicFromFilenameMixin
from .methods.add_to_category import _AddToCategoryMixin
from .methods.balance_resource_distribution import _BalanceResourceDistributionMixin
from .methods.reclassify_by_relevance import _ReclassifyByRelevanceMixin
from .methods.check_grade_match import _CheckGradeMatchMixin
from .methods.apply_subjective_intent_filter import _ApplySubjectiveIntentFilterMixin
from .methods.is_vague_grade_query import _IsVagueGradeQueryMixin
from .methods.apply_flexible_grade_filter import _ApplyFlexibleGradeFilterMixin
from .methods.get_empty_result import _GetEmptyResultMixin
from .methods.extract_query_conditions import _ExtractQueryConditionsMixin
from .methods.extract_resource_types_from_query import _ExtractResourceTypesFromQueryMixin
from .methods.extract_question_type import _ExtractQuestionTypeMixin
from .methods.deduplicate_results import _DeduplicateResultsMixin
from .methods.get_summary import _GetSummaryMixin
from .methods.extract_core_theme import _ExtractCoreThemeMixin
from .methods.extract_theme_with_llm import _ExtractThemeWithLlmMixin
from .methods.extract_theme_with_keywords import _ExtractThemeWithKeywordsMixin
from .methods.extract_query_context_with_llm import _ExtractQueryContextWithLlmMixin
from .methods.get_theory_resources import _GetTheoryResourcesMixin

class ResourceRetriever(_InitMixin, _DetectQueryIntentsMixin, _EnhanceQueryDynamicallyMixin, _BasicQueryEnhancementMixin, _AdjustRetrievalCountMixin, _RetrieveMixin, _ApplyAiRerankMixin, _ApplyUnifiedRankingMixin, _CheckVectorDbExistsMixin, _GenerateQueryEmbeddingMixin, _MergeMultiThemeResultsMixin, _CheckThemeRelevanceWithLlmMixin, _CheckKnowledgePointConsistencyMixin, _ClassifyResultsMixin, _DynamicClassifyResourceMixin, _ApplyGradeFilterMixin, _ApplyTopicExclusionMixin, _ApplyQuantityLimitMixin, _GetMetadataMixin, _GetDistanceMixin, _CreateResourceMixin, _CalculateOverallScoreMixin, _ProcessExerciseResourceMixin, _ProcessGgbResourceMixin, _ProcessSyllabusResourceMixin, _ProcessLessonPlanResourceMixin, _ProcessCoursewareResourceMixin, _ProcessLessonCaseResourceMixin, _ExtractTopicFromFilenameMixin, _AddToCategoryMixin, _BalanceResourceDistributionMixin, _ReclassifyByRelevanceMixin, _CheckGradeMatchMixin, _ApplySubjectiveIntentFilterMixin, _IsVagueGradeQueryMixin, _ApplyFlexibleGradeFilterMixin, _GetEmptyResultMixin, _ExtractQueryConditionsMixin, _ExtractResourceTypesFromQueryMixin, _ExtractQuestionTypeMixin, _DeduplicateResultsMixin, _GetSummaryMixin, _ExtractCoreThemeMixin, _ExtractThemeWithLlmMixin, _ExtractThemeWithKeywordsMixin, _ExtractQueryContextWithLlmMixin, _GetTheoryResourcesMixin):
    """资源检索器"""

    COLLECTION_NAME = "math_resources"
    DEFAULT_N_RESULTS = 500

    def _ensure_collection_ready_for_theme(self, theme: str):
        """
        根据主题获取正确的板块集合

        Args:
            theme: 主题名称

        Returns:
            (collection, early_result): 集合对象和可能的早期结果
        """
        print(f"🔍 为主题 '{theme}' 获取板块集合...")
        if not self._check_vector_db_exists():
            print("⚠️  向量数据库不存在，尝试构建...")
            if not self.vector_db_builder.build_vector_database():
                print("❌ 向量数据库构建失败")
                return None, self._get_empty_result()

        client = self.vector_db_builder.get_chroma_client()
        self.vector_db_builder.get_embedding_model()

        # 根据主题判断板块
        from app.core.vector_database_builder import VectorDatabaseBuilder
        board_collection_name = VectorDatabaseBuilder.get_collection_name_by_theme(
            theme, self.knowledge_hierarchy
        )
        print(f"🎯 根据主题 '{theme}' 选择板块集合: {board_collection_name}")

        try:
            collection = client.get_collection(name=board_collection_name)
            print(f"✅ 成功获取集合: {board_collection_name}")
            return collection, None
        except Exception as e:
            print(f"⚠️ 集合 {board_collection_name} 不存在，尝试使用默认集合: {self.COLLECTION_NAME}")
            try:
                collection = client.get_collection(name=self.COLLECTION_NAME)
                print(f"✅ 成功获取默认集合: {self.COLLECTION_NAME}")
                return collection, None
            except Exception:
                print(f"❌ 默认集合也不存在，向量数据库可能需要重建")
                return None, self._get_empty_result()

    def _calculate_exclusion_factor(self, theme: str, title: str, doc: str, all_themes: List[str]) -> float:
        """
        计算资源的排除因子

        Args:
            theme: 主题名称
            title: 资源标题
            doc: 资源内容
            all_themes: 所有主题列表

        Returns:
            排除因子，0.0表示完全排除，1.0表示不排除
        """
        query_features = getattr(self, "_current_query_features", {})
        exclude_keywords = query_features.get("exclude_keywords", [])

        if not exclude_keywords:
            return 1.0

        all_info = f"{title} {doc}"
        for keyword in exclude_keywords:
            if keyword in all_info:
                return 0.0

        return 1.0

def retrieve_resources(query: str, intent: str = "search") -> Dict[str, Any]:
    """
    根据查询和意图检索相关资源（向后兼容接口）

    Args:
        query: 用户查询
        intent: 用户意图

    Returns:
        检索结果字典
    """
    retriever = ResourceRetriever()

    # V53.12改进：从查询中提取资源类型
    # V56.0改进：扩展资源类型关键词，提高识别准确率
    # V56.1改进：扩展课例相关关键词，提高课例资源识别率
    # 支持多个资源类型的查询，如"课件和教案"
    resource_types = []
    resource_type_keywords = {
        "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课"],
        "教学大纲": ["教学大纲", "大纲", "课程标准"],
        "课件": ["课件", "PPT", "幻灯片", "演示文稿"],
        "课例": ["课例", "教学视频", "课堂实录", "视频", "教学案例", "课堂案例", "讲解", "示范课", "公开课", "观摩课"],
        "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "演示", "动画"],
        "习题": ["习题", "题目", "练习题", "练习", "试题", "测试题", "计算题", "应用题", "填空题", "选择题", "解答题", "证明题", "分层练习", "简单练习"],
        "资料": ["资料", "资源", "教学资源", "教学资料"]
    }

    # 检查查询中是否包含资源类型关键词
    for resource_type, keywords in resource_type_keywords.items():
        if any(kw in query for kw in keywords):
            resource_types.append(resource_type)

    # 去重
    resource_types = list(set(resource_types))

    if resource_types:
        print(f"V53.12识别到资源类型: {resource_types}")

    return retriever.retrieve(query, intent, resource_types=resource_types if resource_types else None)
