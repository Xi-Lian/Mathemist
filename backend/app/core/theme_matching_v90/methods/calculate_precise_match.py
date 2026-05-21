from .._shared import *


class _CalculatePreciseMatchMixin:
    def calculate_precise_match(
        self,
        query: str,
        lesson_title: str,
        lesson_content: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        V10.0：多维度评估，解决"单点依赖"问题

        改进：
        - 引入多维度评估指标
        - 综合考虑资源质量、完整性等因素
        - 实现更全面的资源评估
        """
        # 解析教案结构
        structured = self._parse_lesson_plan(lesson_content)

        # V11.3：添加调试日志，检查教案解析结果
        print(f"\n📊 教案解析结果:")
        print(f"  - 教学目标长度: {len(structured.get('objectives', ''))}")
        print(f"  - 重难点长度: {len(structured.get('key_points', ''))}")
        print(f"  - 教学过程长度: {len(structured.get('process', ''))}")
        print(f"  - 完整内容长度: {len(structured.get('full_content', ''))}")

        # 提取查询主题
        query_themes = self._extract_query_themes(query)

        # 匹配主题
        core_theme = None
        related_themes = []
        mentioned_themes = []
        max_match_score = 0.0
        match_explanations = []
        all_matches = []

        for theme in query_themes:
            # 使用精准匹配计算
            match_result = self._match_single_theme_precise(
                theme, structured, lesson_title, lesson_content, query_themes, metadata
            )

            if match_result:
                match_level = match_result["level"]
                match_score = match_result["score"]
                all_matches.append(match_result)

                if match_level == "core":
                    core_theme = match_result["theme"]
                    match_explanations.append(f"{match_result['theme']}(核心主题)")
                elif match_level == "related":
                    related_themes.append(match_result["theme"])
                    match_explanations.append(f"{match_result['theme']}(相关主题)")
                else:
                    mentioned_themes.append(match_result["theme"])
                    match_explanations.append(f"{match_result['theme']}(提及主题)")

                # 更新最大匹配分数
                if match_score > max_match_score:
                    max_match_score = match_score

        # 计算动态阈值
        core_theme_count = 1 if core_theme else 0
        dynamic_threshold = self._calculate_dynamic_threshold(query, core_theme_count)

        # 确定匹配级别和相关性分数
        if core_theme:
            match_level = "core"
            # 核心主题：0.85-0.95
            relevance_score = 0.85 + (max_match_score - 0.85) * 0.5 if max_match_score > 0.85 else 0.85
            should_show = True
        elif related_themes:
            # V9.2：应用动态阈值过滤
            # 计算相关主题的平均分数
            avg_related_score = max_match_score  # 简化计算

            if avg_related_score >= dynamic_threshold:
                match_level = "related"
                # 相关主题：0.60-0.80
                relevance_score = 0.60 + max_match_score * 0.2
                should_show = True
            else:
                # 低于阈值，降级为扩展主题
                match_level = "extended"
                # 扩展主题：0.30-0.55
                relevance_score = 0.30 + max_match_score * 0.25
                should_show = relevance_score > 0.3
                # 将相关主题移到提及主题
                mentioned_themes.extend([t for t in related_themes])
                related_themes = []
        elif mentioned_themes:
            match_level = "mentioned"
            # 提及主题：0.30-0.55
            relevance_score = 0.30 + max_match_score * 0.25
            should_show = relevance_score > 0.4  # 提高提及主题的阈值，确保只返回更相关的资源
        else:
            # 未匹配到主题
            match_level = "none"
            relevance_score = 0.0
            should_show = False

        # 确定展示级别
        display_level = self._get_display_level(relevance_score)

        # 确定领域分类
        domain = self._determine_domain(core_theme, related_themes, lesson_title, lesson_content)

        # V10.0：计算多维度评估指标
        resource_quality = self._calculate_resource_quality(lesson_title, lesson_content, structured)
        content_completeness = self._calculate_content_completeness(structured)
        teaching_value = self._calculate_teaching_value(structured)
        comprehensiveness = self._calculate_comprehensiveness(structured)

        # V11.3：添加调试日志，显示多维度评估指标
        print(f"\n📈 多维度评估指标:")
        print(f"  - 资源质量: {resource_quality:.2f}")
        print(f"  - 内容完整性: {content_completeness:.2f}")
        print(f"  - 教学价值: {teaching_value:.2f}")
        print(f"  - 综合性: {comprehensiveness:.2f}")

        # V11.0：计算概念层级因子（取所有匹配主题的平均值）
        concept_hierarchy_factor = 0.5  # 默认值
        if all_matches:
            hierarchy_factors = []
            for match in all_matches:
                matched_theme = match["theme"]
                # 计算查询主题与匹配主题之间的层级关系
                factor = self._calculate_concept_hierarchy_factor(query_themes[0] if query_themes else "", matched_theme)
                hierarchy_factors.append(factor)
            if hierarchy_factors:
                concept_hierarchy_factor = sum(hierarchy_factors) / len(hierarchy_factors)

        # 计算综合得分
        overall_score = self._calculate_overall_score(relevance_score, resource_quality, content_completeness, teaching_value, comprehensiveness)

        # 基于综合得分更新展示级别
        display_level = self._get_display_level(overall_score)
        # V61.0改进：提高阈值，确保资源相关性
        should_show = overall_score > 0.30 and relevance_score > 0.30

        explanation = f"匹配级别: {match_level}, 展示级别: {display_level}, " + "; ".join(match_explanations) if match_explanations else "未匹配到主题"

        return {
            "relevance_score": round(relevance_score, 2),
            "overall_score": round(overall_score, 2),  # V10.0：综合得分
            "matched_themes": [match["theme"] for match in all_matches] if all_matches else ([core_theme] if core_theme else related_themes + mentioned_themes),
            "core_theme": core_theme,
            "related_themes": related_themes,
            "mentioned_themes": mentioned_themes,
            "is_core_match": bool(core_theme),
            "match_level": match_level,
            "domain": domain,
            "explanation": explanation,
            "should_show": should_show,
            "display_level": display_level,
            # V10.0：多维度评估指标
            "resource_quality": round(resource_quality, 2),
            "content_completeness": round(content_completeness, 2),
            "teaching_value": round(teaching_value, 2),
            "comprehensiveness": round(comprehensiveness, 2),
            # V11.0：概念层级因子
            "concept_hierarchy_factor": round(concept_hierarchy_factor, 2)
        }