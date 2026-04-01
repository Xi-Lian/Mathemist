from .._shared import *
from ..retrieve_helpers.context import (
    apply_loose_mode,
    ensure_collection_ready,
    extract_query_context,
    prepare_runtime_context,
    validate_resource_types,
)
from ..retrieve_helpers.multi_theme import execute_multi_theme_retrieval
from ..retrieve_helpers.postprocess import (
    apply_difficulty_filter,
    apply_quantity_limit,
    apply_question_type_filter,
    prioritize_pure_function_results,
)
from ..retrieve_helpers.single_theme import (
    execute_single_theme_retrieval,
    postprocess_single_theme_results,
)


class _RetrieveMixin:
    def retrieve(
        self,
        query: str,
        intent: str = "search",
        n_results: int = None,
        resource_types: List[str] = None,
        quantity_limit: Optional[int] = None,
        grade_info: Optional[Dict[str, Any]] = None,
        clarified_topic: Optional[Dict[str, Any]] = None,
        difficulty_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        根据查询和意图检索相关资源

        Args:
            query: 用户查询
            intent: 用户意图
            n_results: 返回结果数量，默认为50
            resource_types: 用户明确提到的资源类型列表（用于精准检索）
            quantity_limit: V33.0 数量限制
            grade_info: V33.0 年级信息
            clarified_topic: V33.0 澄清后的主题信息
            difficulty_info: V33.0 难度信息

        Returns:
            检索结果字典，包含各类资源
        """
        try:
            print(" 资源检索开始")
            print(f"📝 查询: {query}")
            print(f"🎯 意图: {intent}")
            print(f"📋 资源类型: {resource_types}")
            print(f"📋 V33.0数量限制: {quantity_limit}")
            print(f"📋 V33.0年级信息: {grade_info}")
            print(f"📋 V33.0主题澄清: {clarified_topic}")
            print(f"📋 V33.0难度信息: {difficulty_info}")

            self._current_query = query
            resource_types, early_result = validate_resource_types(self, resource_types)
            if early_result is not None:
                return early_result

            quantity_limit = apply_loose_mode(self, query, quantity_limit)
            prepare_runtime_context(
                self,
                query,
                quantity_limit,
                grade_info,
                clarified_topic,
                difficulty_info,
            )

            collection, early_result = ensure_collection_ready(self)
            if early_result is not None:
                return early_result

            query_context, early_result = extract_query_context(self, query, quantity_limit)
            if early_result is not None:
                return early_result

            core_theme = query_context["core_theme"]
            core_themes = query_context["core_themes"]
            question_type = query_context["question_type"]
            difficulty = query_context["difficulty"]
            grade = query_context["grade"]
            exam_form = query_context["exam_form"]
            quantity_limit = query_context["quantity_limit"]

            if len(core_themes) > 1:
                results = execute_multi_theme_retrieval(
                    self,
                    collection,
                    query,
                    core_themes,
                    n_results,
                    resource_types,
                    question_type,
                )
            else:
                _, core_theme, results = execute_single_theme_retrieval(
                    self,
                    collection,
                    query,
                    core_theme,
                    n_results,
                    resource_types,
                    question_type,
                )
                results = postprocess_single_theme_results(self, query, results, resource_types, core_theme)

            if not (results and results.get("documents") and results["documents"][0]):
                print("ℹ️ 查询完成，但未命中任何资源")
                return self._get_empty_result()

            results = apply_difficulty_filter(results, difficulty_info, self._current_quantity_limit)
            results = apply_question_type_filter(results, question_type, self._current_quantity_limit)
            results = prioritize_pure_function_results(self, query, results, quantity_limit)
            results = apply_quantity_limit(results, quantity_limit, core_theme, query, resource_types)

            if results.get("documents") and results["documents"][0]:
                print(f"     ✅ 找到 {len(results['documents'][0])} 条结果")
                for i in range(min(3, len(results["documents"][0]))):
                    meta = results["metadatas"][0][i]
                    print(f"       - 结果{i + 1}: 题目类型={meta.get('题目类型', '未知')}, 来源={meta.get('source_file', '未知')}")
            else:
                print("     ❌ 未找到结果")

            print(f"📊 查询返回 {len(results['documents'][0])} 条结果")
            question_type = self._extract_question_type(query)
            if question_type:
                print(f"🔍 V43.0提取到题目类型: {question_type}")

            classified_resources = self._classify_results(
                results,
                resource_types,
                core_theme,
                query,
                question_type,
                grade,
                difficulty,
                exam_form,
            )

            if core_theme:
                print(f"\n🔍 V8.2主题精准匹配（核心主题: {core_theme}）...")
                all_resources = []
                for category in classified_resources:
                    if isinstance(classified_resources[category], list):
                        for resource in classified_resources[category]:
                            if isinstance(resource, dict):
                                resource["_category"] = category
                                all_resources.append(resource)
                            else:
                                print(f"   ⚠️ 跳过非字典资源: {type(resource)}")

                core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                broad_themes = {"数学", "代数", "几何", "统计", "概率"}
                filtered_themes = [t for t in core_themes if t not in broad_themes]
                if len(filtered_themes) < len(core_themes):
                    print(f"   ⚠️ 过滤过于宽泛的主题: {set(core_themes) - set(filtered_themes)}")
                    core_theme = ",".join(filtered_themes) if filtered_themes else core_themes[0]
                    print(f"   ✅ 过滤后的核心主题: {core_theme}")

                visible_resources = [r for r in all_resources if r.get("should_show", True)]
                hidden_resources = [r for r in all_resources if not r.get("should_show", True)]
                print(f"   🔍 V31.0 DEBUG: visible_resources数量={len(visible_resources)}, hidden_resources数量={len(hidden_resources)}")

                balanced_resources = self._balance_resource_distribution(visible_resources, core_theme, query)
                classified_resources = self._reclassify_by_relevance(balanced_resources, core_theme)
                classified_resources["_hidden_resources"] = hidden_resources
                classified_resources["_hidden_count"] = len(hidden_resources)
                classified_resources["_total_count"] = len(all_resources)
                print(
                    f"   ✅ V8.3排序完成：核心主题优先，共{len(balanced_resources)}个可见资源（隐藏{len(hidden_resources)}个，总计{len(all_resources)}个）"
                )
            else:
                query_features = getattr(self, "_current_query_features", {})
                if query_features.get("has_content_requirement"):
                    print("\n🔍 V9.1应用内容匹配评分（无核心主题）...")
                    for category in classified_resources:
                        for resource in classified_resources[category]:
                            if "content_features" in resource:
                                content_score = self.content_extractor.calculate_content_match_score(
                                    resource["content_features"], query_features
                                )
                                original_relevance = resource.get("relevance", 0)
                                resource["relevance"] = original_relevance * 0.7 + content_score * 0.3
                                resource["content_match_score"] = content_score

                for category in classified_resources:
                    if classified_resources[category]:
                        classified_resources[category].sort(key=lambda x: -x.get("relevance", 0))

                classified_resources["_hidden_resources"] = []
                classified_resources["_hidden_count"] = 0
                classified_resources["_total_count"] = sum(
                    len(resources) for resources in classified_resources.values() if isinstance(resources, list)
                )

            classified_resources = self._apply_ai_rerank_stage(
                classified_resources,
                query,
                intent,
                resource_types,
                core_theme,
            )

            classified_resources = self._apply_unified_ranking(
                classified_resources,
                quantity_limit,
                query=query,
                resource_types=resource_types,
            )

            scope_notice = getattr(self, "_current_scope_notice", None)
            if scope_notice:
                classified_resources["_scope_notice"] = scope_notice

            print(f"✅ 检索完成: {self._get_summary(classified_resources)}")
            return classified_resources

        except Exception as e:
            print(f"❌ 资源检索失败: {str(e)}")
            return self._get_empty_result()



