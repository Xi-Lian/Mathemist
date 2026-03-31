from .._shared import *


class _CalculateExclusionFactorMixin:
    def _calculate_exclusion_factor(self, theme: str, lesson_title: str, lesson_content: str, query_themes: List[str] = None, metadata: Dict[str, Any] = None) -> float:
        """
        V18.0：计算排除词因子 - 智能版
        
        如果包含排除词，返回0.0的因子，直接排除
        
        V18.0改进：
        1. 对于组合查询（如"二次函数和一次函数"），不过滤掉查询主题相关的排除词
        2. 对于单一主题查询，严格过滤掉包含其他主题关键词的资源
        3. 增加对习题内容的智能分析，避免误过滤
        4. V27.0：添加路径冲突检测，根据文件路径中的章节信息判断主题冲突
        
        Args:
            theme: 当前主题
            lesson_title: 教案标题
            lesson_content: 教案内容
            query_themes: 查询的主题列表，用于过滤与其他查询主题相关的排除词
            metadata: 资源元数据，包含source_file等信息
        
        Returns:
            float: 排除词因子 (0.0-1.0)
        """
        exclusion_words = self.theme_exclusion_words.get(theme, [])
        if not exclusion_words:
            return 1.0
        
        # V62.0改进：导入re模块用于正则表达式匹配
        import re
        
        # V62.0改进：路径冲突检测
        # 检查文件路径中的章节信息，判断是否存在主题冲突
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
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在三角函数章节，但主题 '{theme}' 不是三角函数")
                return 0.0
            
            # V62.0改进：检查是否在二次函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配2.3章节
            quadratic_pattern = r'教案[\\\/](第二章|2\.3|2-3|二次函数)[\\\/]'
            is_in_quadratic_chapter = bool(re.search(quadratic_pattern, source_file))
            
            # 检查当前主题是否与二次函数相关
            quadratic_keywords = ["二次函数", "抛物线", "顶点", "对称轴"]
            current_theme_is_quadratic = any(quad_keyword in theme for quad_keyword in quadratic_keywords)
            
            # 如果资源在二次函数章节，但当前主题不是二次函数，则存在路径冲突
            if is_in_quadratic_chapter and not current_theme_is_quadratic:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在二次函数章节，但主题 '{theme}' 不是二次函数")
                return 0.0
            
            # V62.0改进：检查是否在指数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.1和4.2章节
            exponential_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.1|4\.2|4-1|4-2|指数函数)[\\\/]'
            is_in_exponential_chapter = bool(re.search(exponential_pattern, source_file))
            
            # 检查当前主题是否与指数函数相关
            exponential_keywords = ["指数函数", "指数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            
            # 如果资源在指数函数章节，但当前主题不是指数函数，则存在路径冲突
            if is_in_exponential_chapter and not current_theme_is_exponential:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在指数函数章节，但主题 '{theme}' 不是指数函数")
                return 0.0
            
            # V62.0改进：检查是否在对数函数章节（精确匹配，避免误判）
            # 使用正则表达式精确匹配4.3和4.4章节
            logarithmic_pattern = r'教案[\\\/]第四章[^\\\/]*[\\\/](4\.3|4\.4|4-3|4-4)[\\\/]'
            is_in_logarithmic_chapter = bool(re.search(logarithmic_pattern, source_file))
            
            # 检查当前主题是否与对数函数相关
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在对数函数章节，但当前主题不是对数函数，则存在路径冲突
            if is_in_logarithmic_chapter and not current_theme_is_logarithmic:
                print(f"      ⚠️ V62.0路径冲突检测: '{lesson_title}' 在对数函数章节，但主题 '{theme}' 不是对数函数")
                return 0.0
        
        # V18.0改进：智能过滤排除词
        # 对于组合查询，如果排除词是查询主题之一，则不过滤
        filtered_exclusion_words = []
        if query_themes:
            for word in exclusion_words:
                # 检查排除词是否是查询主题之一
                is_query_theme = False
                for query_theme in query_themes:
                    if word in query_theme or query_theme in word:
                        is_query_theme = True
                        break
                
                if not is_query_theme:
                    filtered_exclusion_words.append(word)
        else:
            filtered_exclusion_words = exclusion_words
        
        print(f"      🔍 主题 '{theme}' 的排除词: {exclusion_words}")
        print(f"      🔍 查询主题: {query_themes}")
        print(f"      🔍 过滤后的排除词: {filtered_exclusion_words}")
        
        full_text = f"{lesson_title} {lesson_content}".lower()
        
        # V54.2改进：根据资源类型调整排除词检查策略
        # 教案、课件、GGB等不同类型的资源应该有不同的检查策略
        resource_type = metadata.get('resource_type', 'unknown') if metadata else 'unknown'
        is_lesson_plan = resource_type == 'lesson_plan' or '教案' in lesson_title or '教学设计' in lesson_title or '导学案' in lesson_title
        is_courseware = resource_type == 'courseware' or '课件' in lesson_title or 'PPT' in lesson_title
        is_ggb = resource_type == 'ggb' or 'GGB' in lesson_title or 'GeoGebra' in lesson_title
        is_syllabus = resource_type == 'syllabus' or '教学大纲' in lesson_title or '大纲' in lesson_title
        is_lesson_case = resource_type == 'lesson_case' or '课例' in lesson_title or '教学案例' in lesson_title
        is_exercise = resource_type == 'exercise' or '习题' in lesson_title or '题目' in lesson_title
        
        # V63.1改进：根据资源类型调整章节路径检查
        # 不同类型的资源可能有不同的路径格式
        is_in_correct_chapter = False
        if metadata and metadata.get('source_file'):
            source_file = metadata.get('source_file', '')
            
            # 检查是否在指数函数章节（4.1或4.2）
            # V63.0修复：使用更简单的正则表达式，避免[^\/]*不匹配中文和空格的问题
            # V63.1改进：支持不同资源类型的路径格式
            exponential_patterns = [
                r'教案.*4\.[12].*指数函数',
                r'课件.*4\.[12].*指数函数',
                r'GGB.*4\.[12].*指数函数',
                r'课例.*4\.[12].*指数函数',
                r'教学大纲.*4\.[12].*指数函数'
            ]
            
            logarithmic_patterns = [
                r'教案.*4\.[34].*对数函数',
                r'课件.*4\.[34].*对数函数',
                r'GGB.*4\.[34].*对数函数',
                r'课例.*4\.[34].*对数函数',
                r'教学大纲.*4\.[34].*对数函数'
            ]
            
            is_in_exponential_chapter = any(bool(re.search(pattern, source_file)) for pattern in exponential_patterns)
            is_in_logarithmic_chapter = any(bool(re.search(pattern, source_file)) for pattern in logarithmic_patterns)
            
            # 检查当前主题
            exponential_keywords = ["指数函数", "指数"]
            logarithmic_keywords = ["对数函数", "对数"]
            current_theme_is_exponential = any(exp_keyword in theme for exp_keyword in exponential_keywords)
            current_theme_is_logarithmic = any(log_keyword in theme for log_keyword in logarithmic_keywords)
            
            # 如果资源在正确的章节路径中，标记为正确章节
            if is_in_exponential_chapter and current_theme_is_exponential:
                is_in_correct_chapter = True
                print(f"      ✅ V63.0章节匹配：资源在指数函数章节，主题也是指数函数，放宽排除词检查")
            elif is_in_logarithmic_chapter and current_theme_is_logarithmic:
                is_in_correct_chapter = True
                print(f"      ✅ V63.0章节匹配：资源在对数函数章节，主题也是对数函数，放宽排除词检查")
        
        # V18.0改进：对于习题资源，进行更智能的排除词检查
        # 检查是否包含任何排除词
        for word in filtered_exclusion_words:
            if word.lower() in full_text:
                # V61.0改进：严格检查教案资源的排除词
                # V63.0改进：如果资源在正确的章节路径中，放宽排除词检查
                # V63.1改进：根据资源类型调整排除词检查策略
                if is_lesson_plan:
                    # 如果排除词在标题中，直接排除（即使在正确章节也排除）
                    if word.lower() in lesson_title.lower():
                        print(f"      ⚠️ V61.0教案资源严格过滤：'{lesson_title}' 标题包含排除词 '{word}'，直接排除")
                        return 0.0
                    
                    # V63.0改进：如果资源在正确的章节路径中，放宽排除词检查
                    if is_in_correct_chapter:
                        print(f"      ✅ V63.0放宽检查：'{lesson_title}' 在正确章节路径中，包含排除词 '{word}' 但允许通过")
                        continue
                    
                    # 如果排除词在内容中，检查是否是主要知识点
                    # 通过检查排除词周围的上下文判断
                    # 简单判断：如果排除词出现次数较多，说明是主要知识点
                    word_count = full_text.lower().count(word.lower())
                    if word_count >= 3:
                        print(f"      ⚠️ V61.0教案资源严格过滤：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，排除")
                        return 0.0
                elif is_courseware or is_ggb or is_syllabus or is_lesson_case:
                    # 对于课件、GGB、教学大纲、课例资源，更宽松地处理排除词
                    # 这些资源类型通常包含多个主题的内容
                    print(f"      ✅ V63.1放宽检查：'{lesson_title}' 是{resource_type}资源，包含排除词 '{word}' 但允许通过")
                    continue
                elif is_exercise:
                    # V18.0改进：对于习题资源，进行更智能的排除词检查
                    # 对于习题资源，检查排除词是否是主要知识点
                    # 通过检查排除词出现的次数来判断
                    word_count = full_text.lower().count(word.lower())
                    if word_count >= 2:
                        print(f"      ⚠️ V18.0习题资源过滤：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，排除")
                        return 0.0
                    else:
                        print(f"      ✅ V18.0习题资源放宽检查：'{lesson_title}' 内容中排除词 '{word}' 出现{word_count}次，允许通过")
                        continue
                
                # V18.0改进：对于组合查询，如果资源同时包含查询主题的关键词，则不过滤
                if query_themes and len(query_themes) > 1:
                    # 检查资源是否包含查询主题的关键词
                    has_query_theme_keyword = False
                    for query_theme in query_themes:
                        if query_theme.lower() in full_text:
                            has_query_theme_keyword = True
                            break
                    
                    if has_query_theme_keyword:
                        print(f"      ✅ V18.0智能过滤：'{lesson_title}' 包含排除词 '{word}'，但同时包含查询主题关键词，允许通过")
                        continue
                
                # 包含排除词，返回0.0的因子，直接排除
                print(f"      ⚠️ 排除：'{lesson_title}' 包含排除词 '{word}' (主题: {theme})")
                return 0.0
        
        return 1.0
