from .._shared import *
import re
from ..classify_results_helpers.filters import calculate_relevance_boost, matches_exercise_question_type
from ..classify_results_helpers.resource_type import (
    init_classified,
    matches_requested_resource_type,
    normalize_resource_type,
)

DIFFICULTY_KEYWORD_POLICY = {
    "基础": ["基础", "简单", "入门", "初级", "1", "2"],
    "中等": ["中等", "一般", "普通", "常见", "3"],
    "拔高": ["拔高", "难", "困难", "挑战", "压轴", "4", "5"],
}
PROOF_KEYWORDS = ["求证", "证明", "证明题", "推导", "推导题"]
PROOF_QUERY_HINTS = ["单调性", "证明"]
PROOF_KNOWLEDGE_HINTS = ["单调性", "单调", "增函数", "减函数"]


class _ClassifyResultsMixin:
    def _classify_results(
        self,
        results: Dict[str, Any],
        resource_types: List[str] = None,
        core_theme: str = "",
        query: str = "",
        question_type: str = "",
        grade: str = "",
        difficulty: str = "",
        exam_form: str = "",
    ) -> Dict[str, Any]:
        """
        对检索结果进行分类
        """
        query_features = getattr(self, "_current_query_features", {})
        classified = init_classified()

        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = self._get_metadata(results, i)
                distance = self._get_distance(results, i)
                resource_type = normalize_resource_type(metadata, metadata.get("resource_type", "theory"))

                print(f"   🔍 V19.3调试 - 资源类型: '{resource_type}', 标题: '{metadata.get('title', '未知')}'")
                matched = matches_requested_resource_type(resource_type, resource_types)
                if not matched:
                    continue

                relevance_info = calculate_relevance_boost(
                    self,
                    classified,
                    metadata,
                    doc,
                    distance,
                    resource_type,
                    resource_types,
                    core_theme,
                    query,
                    question_type,
                    grade,
                    difficulty,
                )
                relevance = relevance_info["relevance"]
                contains_core_theme = relevance_info["contains_core_theme"]

                if resource_type == "exercise" and question_type:
                    if not matches_exercise_question_type(classified, metadata, doc, query, question_type):
                        continue

                if resource_type == "exercise":
                    is_consistent = self._check_knowledge_point_consistency(metadata, core_theme, doc, query, relevance)
                    if not is_consistent:
                        if self._should_soft_keep_exercise(metadata, query, resource_types, question_type, relevance):
                            print(f"   ✅ V96.0保留语义相关但知识点未精确对齐的习题: '{metadata.get('title', '未知')}'")
                            metadata = dict(metadata)
                            metadata["_soft_kept_exercise"] = True
                        else:
                            print(f"   ⚠️ V15.0跳过不一致的习题: '{metadata.get('title', '未知')}' (来源: {metadata.get('source_file', '')})")
                            continue
                    if not self._passes_exercise_filters(metadata, doc, query, classified, grade, difficulty, exam_form):
                        continue

                if self._is_special_resource_request(resource_type, resource_types):
                    print(f"   ✅ V87.0调试 - 资源类型确认: {resource_type}")

                resource = self._create_resource(doc, metadata, distance, resource_type, core_theme, resource_types, query, question_type)
                if resource_type == "exercise" and metadata.get("_soft_kept_exercise"):
                    original_relevance = resource.get("relevance", 0)
                    resource["relevance"] = max(0.0, original_relevance - 0.08)
                    resource["soft_kept_exercise"] = True
                self._apply_exercise_content_requirements(resource, resource_type, metadata, doc, query_features, query)

                if resource.get("should_show", True):
                    self._add_resource_to_classified(classified, resource, resource_type, resource_types, doc, metadata, query)
                else:
                    print(f"   ⚠️ V30.5跳过should_show=False的资源: '{resource.get('title', '未知')}'")

        return self._finalize_classified_results(classified, query)

    def _should_soft_keep_exercise(self, metadata, query, resource_types, question_type, relevance):
        explicit_exercise_keywords = ["习题", "题目", "练习", "选择题", "填空题", "解答题", "证明题", "测试题"]
        explicit_exercise_query = any(keyword in (query or "") for keyword in explicit_exercise_keywords)
        requested_exercise = any(rt in ["习题", "exercise"] for rt in (resource_types or []))
        if not (explicit_exercise_query or requested_exercise):
            return False

        if relevance >= 0.18:
            return True

        title = metadata.get("title", "") or ""
        source_file = metadata.get("source_file", "") or ""
        knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "") or ""
        searchable_text = f"{title} {source_file} {knowledge_tags}"

        query_terms = [term for term in re.split(r"[\s,，。；、]+", query or "") if len(term) >= 2]
        query_terms = [
            term for term in query_terms
            if term not in explicit_exercise_keywords and term not in ["推荐几道", "推荐", "给我", "找几道", "几道"]
        ]
        if question_type:
            query_terms = [term for term in query_terms if term != question_type]

        return any(term in searchable_text for term in query_terms)

    def _passes_exercise_filters(self, metadata, doc, query, classified, grade, difficulty, exam_form):
        if not self._passes_grade_policy(metadata, doc, grade):
            return False
        if not self._passes_difficulty_policy(metadata, classified, difficulty):
            return False
        if not self._passes_exam_form_policy(metadata, doc, query, exam_form):
            return False
        return True

    def _passes_grade_policy(self, metadata, doc, grade):
        if not grade:
            return True

        resource_grade = metadata.get("grade", "") or metadata.get("年级", "")
        if not resource_grade:
            return True
        if grade in resource_grade or resource_grade in grade:
            return True

        # 通用放宽：同学段年级允许相邻匹配，不做主题特判硬编码。
        grade_order = {"高一": 1, "高二": 2, "高三": 3}
        query_level = next((v for k, v in grade_order.items() if k in grade), None)
        resource_level = next((v for k, v in grade_order.items() if k in resource_grade), None)
        if query_level is not None and resource_level is not None and abs(query_level - resource_level) <= 1:
            return True

        print(f"   ⚠️ 年级过滤: 资源年级'{resource_grade}'与查询年级'{grade}'不匹配")
        return False

    def _passes_difficulty_policy(self, metadata, classified, difficulty):
        if not difficulty:
            return True

        resource_difficulty = metadata.get("难度（1-5）", "") or metadata.get("difficulty", "") or metadata.get("难度", "")
        if not resource_difficulty:
            return True

        keywords = DIFFICULTY_KEYWORD_POLICY.get(difficulty, [])
        if any(str(keyword) in str(resource_difficulty) for keyword in keywords):
            return True

        current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
        if current_count < 5:
            print(f"   ✅ V95.0资源不足，放宽难度限制: 接受资源难度'{resource_difficulty}'")
            return True

        print(f"   ⚠️ V49.0难度过滤: 资源难度'{resource_difficulty}'与查询难度'{difficulty}'不匹配")
        return False

    def _passes_exam_form_policy(self, metadata, doc, query, exam_form):
        if not exam_form:
            return True

        content = doc + (metadata.get("知识点", "") or "") + (metadata.get("知识点标签", "") or "")
        is_target_proof_query = ("单调性" in query and "证明" in query) or ("奇偶性" in query and "证明" in query)
        if not is_target_proof_query:
            return True

        is_trig_identity = "恒等" in content or ("求证" in content and "=" in content and any(trig in content for trig in ["sin", "cos", "tan"]))
        is_monotonicity_proof = any(keyword in content for keyword in ["单调性", "递增", "递减", "增函数", "减函数", "单调递增", "单调递减"])
        is_parity_proof = any(keyword in content for keyword in ["奇偶性", "奇函数", "偶函数", "奇函数证明", "偶函数证明"])

        if is_trig_identity and not is_monotonicity_proof and not is_parity_proof:
            print("   ⚠️ V50.0证明题过滤: 排除三角恒等式证明，需要单调性或奇偶性证明")
            return False
        return True

    def _apply_exercise_content_requirements(self, resource, resource_type, metadata, doc, query_features, query):
        if resource_type != "exercise" or not query_features.get("has_content_requirement"):
            return

        content_score = self.content_extractor.calculate_content_match_score({}, query_features, metadata, doc)
        original_relevance = resource.get("relevance", 0)
        if original_relevance >= 0.30:
            resource["relevance"] = original_relevance * 0.7 + content_score * 0.3
            resource["content_match_score"] = content_score
            resource["original_relevance"] = original_relevance
        else:
            resource["relevance"] = 0.0
            resource["content_match_score"] = 0.0
            resource["original_relevance"] = original_relevance
            resource["should_show"] = False

        required_type = query_features.get("required_exercise_type")
        if not required_type:
            return
        if required_type == "应用题" or "应用" in query:
            print("   ✅ V52.0应用题查询: 允许所有类型的习题")
            return

        exercise_type = metadata.get("题目类型", "")
        mapped_type = "解答题" if required_type == "计算题" else required_type
        if not exercise_type:
            return
        if not self._is_exercise_type_allowed(mapped_type, exercise_type, metadata, doc, query):
            print(f"   ⚠️ V18.0/V18.4跳过不匹配的习题类型: {exercise_type} != {required_type} (映射为: {mapped_type})")
            resource["should_show"] = False
            return
        print(f"   ✅ V38.0题目类型匹配通过: {mapped_type} <-> {exercise_type}")

    def _is_exercise_type_allowed(self, mapped_type, exercise_type, metadata, doc, query):
        if mapped_type == "证明题":
            return self._matches_proof_type(metadata, exercise_type, doc, query)
        return mapped_type in exercise_type or exercise_type in mapped_type

    def _matches_proof_type(self, metadata, exercise_type, doc, query):
        if any(keyword in doc for keyword in PROOF_KEYWORDS):
            print("   ✅ V46.0证明题关键词匹配: 发现证明关键词")
            return True
        if "解答" not in exercise_type:
            return False
        if any(keyword in doc for keyword in ["证明", "单调性", "求证"]):
            print("   ✅ V46.0证明题匹配: 解答题包含证明内容")
            return True
        if any(keyword in query for keyword in PROOF_QUERY_HINTS):
            print("   ✅ V46.0证明题匹配: 查询包含证明相关词，解答题通过")
            return True
        if "单调性" in query:
            knowledge_tags = metadata.get("知识点标签", "")
            if any(keyword in knowledge_tags for keyword in PROOF_KNOWLEDGE_HINTS):
                print(f"   ✅ V46.0证明题匹配: 知识点标签'{knowledge_tags}'包含单调性相关关键词")
                return True
        print("   ✅ V46.0证明题匹配: 解答题类型，放宽匹配条件")
        return True

    def _is_special_resource_request(self, resource_type, resource_types):
        if not resource_types:
            return False
        if resource_type == "courseware" and any(rt in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"] for rt in resource_types):
            return True
        if resource_type == "lesson_plan" and any(rt in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"] for rt in resource_types):
            return True
        return False

    def _add_resource_to_classified(self, classified, resource, resource_type, resource_types, doc, metadata, query):
        if resource_type == "courseware" and resource_types and any(rt in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"] for rt in resource_types):
            print("   📊 V88.0分类调整 - 课件资源添加到courseware_resources")
            self._add_to_category(classified, "courseware", resource)
            return
        if resource_type == "lesson_plan" and resource_types and any(rt in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"] for rt in resource_types):
            print("   📊 V88.0分类调整 - 教案资源添加到lesson_plan_patterns")
            self._add_to_category(classified, "lesson_plan", resource)
            return

        dynamic_category = self._dynamic_classify_resource(resource, doc, metadata, query)
        if dynamic_category:
            print(f"   📊 V33.0动态分类: {dynamic_category}")
            self._add_to_category(classified, dynamic_category, resource)
        else:
            self._add_to_category(classified, resource_type, resource)

    def _finalize_classified_results(self, classified, query):
        quantity_limit = getattr(self, "_current_quantity_limit", None)
        grade_info = getattr(self, "_current_grade_info", None)
        clarified_topic = getattr(self, "_current_clarified_topic", None)

        print("\n🔍 V52.0年级过滤前资源数量:")
        for category in classified:
            if isinstance(classified[category], list):
                print(f"   📊 {category}: {len(classified[category])} 条资源")

        if grade_info:
            print(f"\n🎓 V33.0应用年级过滤: {grade_info}")
            classified = self._apply_grade_filter(classified, grade_info, query)

        if clarified_topic and clarified_topic.get("should_exclude"):
            print(f"\n🔍 V33.0应用主题排除过滤: {clarified_topic}")
            classified = self._apply_topic_exclusion(classified, clarified_topic)

        if quantity_limit:
            print(f"\n📊 V33.0应用数量限制: {quantity_limit}")
            classified = self._apply_quantity_limit(classified, quantity_limit)

        total_resources = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
        if total_resources == 0:
            classified = self._recover_related_resources(classified, query)
        return classified

    def _recover_related_resources(self, classified, query):
        print("\n⚠️ V95.0资源不足，尝试返回相关主题资源")
        if not hasattr(self, "vector_db_builder"):
            print("   ❌ V95.0无法获取vector_db_builder")
            return classified

        client = self.vector_db_builder.get_chroma_client()
        collection = client.get_collection(name=self.COLLECTION_NAME)
        from app.core.theme_matcher import ThemeMatcher

        theme_matcher = ThemeMatcher()
        detected_themes = theme_matcher.dynamic_theme_detection(query, query)
        if not detected_themes:
            print("   ❌ V95.0未检测到主题")
            return classified

        main_theme = detected_themes[0]["theme"]
        print(f"   🔍 V95.0检测到主题: {main_theme}")
        results = collection.get(where={"resource_type": "exercise"}, limit=20)
        related_resources = []
        for i, metadata in enumerate(results["metadatas"]):
            knowledge_tags = metadata.get("知识点标签", "")
            source_file = metadata.get("source_file", "")
            title = metadata.get("title", "")
            if main_theme in knowledge_tags or main_theme in source_file or main_theme in title:
                related_resources.append(
                    {
                        "id": results["ids"][i],
                        "title": title,
                        "resource_type": "exercise",
                        "relevance": 0.8,
                        "knowledge_tags": knowledge_tags,
                        "source_file": source_file,
                    }
                )

        if related_resources:
            print(f"   ✅ V95.0返回{main_theme}相关资源: {len(related_resources)}条")
            classified["exercise_resources"] = related_resources[:5]
        else:
            print(f"   ❌ V95.0未找到{main_theme}相关资源")
        return classified
