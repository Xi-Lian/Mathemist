from .._shared import *


class _MatchSingleThemePreciseMixin:
    def _match_single_theme_precise(
        self,
        theme: str,
        structured: Dict[str, str],
        lesson_title: str,
        lesson_content: str,
        query_themes: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """
        V11.6：连续匹配度评估，替代刚性判断
        
        改进：
        - 从刚性次数要求改为连续匹配度评估
        - 支持同一主题的多种表达方式
        - 实现平滑的匹配级别过渡
        - V11.6：区分"一般函数概念"和"具体函数概念"
        - V27.0：添加metadata参数，支持路径冲突检测
        - V61.0：在匹配之前先检查路径冲突
        
        Returns:
            包含匹配结果的字典，或None
        """
        # V62.0改进：导入re模块用于正则表达式匹配
        import re
        
        # V61.0改进：在匹配之前先检查路径冲突
        # V62.0改进：修复路径冲突检测逻辑，避免"第四章"同时匹配指数和对数章节
        if metadata and metadata.get('source_file'):
            source_file = metadata.get('source_file', '')
            
            # V62.0改进：检查是否在三角函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配5.4、5.5、5.6章节
            trigonometry_pattern = r'教案[\\\/]第五章[^\\\/]*[\\\/](5\.4|5\.5|5\.6|5-4|5-5|5-6|三角函数)[\\\/]'
            is_in_trigonometry_chapter = bool(re.search(trigonometry_pattern, source_file))
            
            # 检查当前主题是否与三角函数相关
            trigonometry_keywords = ["三角函数", "正弦", "余弦", "正切", "sin", "cos", "tan"]
            current_theme_is_trig = any(trig_keyword in theme for trig_keyword in trigonometry_keywords)
            
            # 如果资源在三角函数章节，但当前主题不是三角函数，则存在路径冲突
            if is_in_trigonometry_chapter and not current_theme_is_trig:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在三角函数章节，但主题 '{theme}' 不是三角函数")
                return None
            
            # V62.0改进：检查是否在二次函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配2.3章节
            quadratic_pattern = r'教案[\\\/](第二章|2\.3|2-3|二次函数)[\\\/]'
            is_in_quadratic_chapter = bool(re.search(quadratic_pattern, source_file))
            
            # 检查当前主题是否与二次函数相关
            quadratic_keywords = ["二次函数", "抛物线", "顶点", "对称轴"]
            current_theme_is_quadratic = any(quad_keyword in theme for quad_keyword in quadratic_keywords)
            
            # 如果资源在二次函数章节，但当前主题不是二次函数，则存在路径冲突
            if is_in_quadratic_chapter and not current_theme_is_quadratic:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在二次函数章节，但主题 '{theme}' 不是二次函数")
                return None
            
            # V62.0改进：检查是否在指数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.1和4.2章节
            exponential_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.1|4\.2|4-1|4-2|指数函数)[\\\/]'
            is_in_exponential_chapter = bool(re.search(exponential_pattern, source_file))
            
            # 检查当前主题是否与指数函数相关
            exponential_keywords = ["指数函数", "指数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            
            # 如果资源在指数函数章节，但当前主题不是指数函数，则存在路径冲突
            if is_in_exponential_chapter and not current_theme_is_exponential:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在指数函数章节，但主题 '{theme}' 不是指数函数")
                return None
            
            # V62.0改进：检查是否在对数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.3和4.4章节
            logarithmic_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.3|4\.4|4-3|4-4)[\\\/]'
            is_in_logarithmic_chapter = bool(re.search(logarithmic_pattern, source_file))
            
            # 检查当前主题是否与对数函数相关
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在对数函数章节，但当前主题不是对数函数，则存在路径冲突
            if is_in_logarithmic_chapter and not current_theme_is_logarithmic:
                print(f"      ⚠️ V61.0路径冲突检测: '{lesson_title}' 在对数函数章节，但主题 '{theme}' 不是对数函数")
                return None
        
        # 提取主题关键词（包括变体和同义词）
        theme_keywords = self._extract_theme_keywords(theme)
        
        # 0. 严格检查标题匹配（标题必须包含完整主题词）
        title_lower = lesson_title.lower()
        theme_lower = theme.lower()
        
        # V11.6：判断是否是"一般函数概念"
        specific_function_types = ["指数", "对数", "幂", "三角", "正弦", "余弦", "正切", "反三角", "二次"]
        is_general_function_concept = theme.startswith("函数的")
        is_specific_function_concept = any(theme.startswith(ft) or (ft in theme and "函数" in theme) for ft in specific_function_types)
        
        # V11.6：检查标题是否包含"具体函数概念"
        title_has_specific_function = any(ft in title_lower for ft in specific_function_types)
        
        # 标题完全匹配或包含完整主题词
        if theme_lower in title_lower:
            # V11.6：如果主题是"一般函数概念"，而标题包含"具体函数概念"，则降级匹配
            if is_general_function_concept and not is_specific_function_concept and title_has_specific_function:
                # 例如："函数的概念"不应该匹配"三角函数的概念"
                # 降级为相关主题匹配
                base_score = 0.70
                weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "related",
                    "score": final_score,
                    "evidence": ["标题包含相关概念（具体函数概念）"]
                }
            
            # 计算权重因子
            # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
            final_score = 0.95 * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "core",
                "score": final_score,
                "evidence": ["标题完全匹配"]
            }
        
        # 检查标题是否包含主题的核心关键词或变体
        core_keywords = self._get_theme_variants(theme)
        for keyword in core_keywords:
            if keyword.lower() in title_lower:
                # V11.6：如果主题是"一般函数概念"，而标题包含"具体函数概念"，则降级匹配
                if is_general_function_concept and not is_specific_function_concept and title_has_specific_function:
                    base_score = 0.65
                    # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
                    weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                    # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
                    if weight_factor == 0.0:
                        return None
                    hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                    final_score = base_score * weight_factor * hierarchy_factor
                    return {
                        "theme": theme,
                        "level": "related",
                        "score": final_score,
                        "evidence": ["标题包含相关概念（具体函数概念）"]
                    }
                
                # 计算权重因子
                # V63.0修复：传递metadata参数，以便检查资源是否在正确的章节路径中
                weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
                # 如果排除词因子为0.0，直接返回None，过滤掉不相关的资源
                if weight_factor == 0.0:
                    return None
                # 计算概念层级因子
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_title)
                final_score = 0.90 * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "core",
                    "score": final_score,
                    "evidence": ["标题核心词匹配"]
                }
        
        # 1. 检查教学目标（核心主题）- 连续评估
        objectives = structured.get("objectives", "")
        core_matches = self._count_keyword_matches(theme_keywords, objectives)
        
        if core_matches >= 3:
            # 高匹配度：核心主题
            base_score = 0.88
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "core",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        elif core_matches == 2:
            # 中等匹配度：强相关主题
            base_score = 0.75
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        elif core_matches == 1:
            # 弱匹配度：相关主题
            base_score = 0.70
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, objectives)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学目标中出现{core_matches}次"]
            }
        
        # 2. 检查教学重难点（相关主题）- 连续评估
        key_points = structured.get("key_points", "")
        important_matches = self._count_keyword_matches(theme_keywords, key_points)
        
        if important_matches >= 3:
            # 高匹配度：相关主题
            base_score = 0.75
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        elif important_matches == 2:
            # 中等匹配度：相关主题
            base_score = 0.65
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        elif important_matches == 1:
            # 弱匹配度：提及主题
            base_score = 0.50
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, key_points)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学重难点中出现{important_matches}次"]
            }
        
        # 3. 检查教学过程（提及主题）- 连续评估
        process = structured.get("process", "")
        process_matches = self._count_keyword_matches(theme_keywords, process)
        
        if process_matches >= 8:
            # 高匹配度：相关主题
            base_score = 0.60
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "related",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        elif process_matches >= 5:
            # 中等匹配度：提及主题
            base_score = 0.45
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        elif process_matches >= 2:
            # 弱匹配度：提及主题
            base_score = 0.35
            weight_factor = self._calculate_weight_factor(theme, lesson_title, lesson_content, query_themes, metadata)
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            # 计算概念层级因子
            hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, process)
            final_score = base_score * weight_factor * hierarchy_factor
            return {
                "theme": theme,
                "level": "mentioned",
                "score": final_score,
                "evidence": [f"教学过程中出现{process_matches}次"]
            }
        
        # 4. 检查主题层级关系（相关主题）- V10.0：连续评估
        if self._is_related_theme(theme, lesson_title, lesson_content):
            # 计算领域距离因子
            distance_factor = self._calculate_domain_distance_factor(theme, lesson_title, lesson_content)
            
            # V10.0：方向控制作为权重因子
            direction_factor = self._calculate_direction_factor(theme, lesson_title, lesson_content)
            
            # 计算综合权重因子
            weight_factor = (distance_factor + direction_factor) / 2
            
            # 如果权重因子为0.0，直接返回None，过滤掉不相关的资源
            if weight_factor == 0.0:
                return None
            
            # 计算概念层级因子
            lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
            if lesson_theme:
                hierarchy_factor = self._calculate_concept_hierarchy_factor(theme, lesson_theme)
            else:
                hierarchy_factor = 1.0
            
            if self._is_downward_recommendation(theme, lesson_title, lesson_content):
                base_score = 0.60
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "related",
                    "score": final_score,  # 应用权重因子
                    "evidence": ["主题层级关系匹配（向下推荐）"]
                }
            else:
                # 向上推荐（子→父）：作为权重因子
                base_score = 0.40
                final_score = base_score * weight_factor * hierarchy_factor
                return {
                    "theme": theme,
                    "level": "mentioned",
                    "score": final_score,  # 应用权重因子
                    "evidence": ["主题层级关系匹配（向上推荐）"]
                }
        
        return None
