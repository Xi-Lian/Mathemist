"""
简化的习题检索模块
利用预分析字段提高检索速度和准确性
"""

import logging

logger = logging.getLogger(__name__)


def simple_exercise_retrieval(
    query,
    core_theme,
    vector_db,
    n_results=50,  # 【V102.0优化】从10增加到50，提高召回率
    resource_types=["exercise"],
    difficulty=None,
    question_type=None
):
    """
    简化的习题检索方法
    
    Args:
        query: 用户查询
        core_theme: 核心主题
        vector_db: 向量数据库客户端
        n_results: 返回结果数量
        resource_types: 资源类型过滤
        difficulty: 难度过滤（可选）
        question_type: 题型过滤（可选）
    
    Returns:
        list: 检索结果（包含score字段）
    """
    # 资源类型映射（中文到英文）
    resource_type_mapping = {
        "习题": "exercise",
        "练习题": "exercise",
        "题目": "exercise",
        "教案": "lesson_plan",
        "课件": "courseware",
        "课例": "lesson_case",
        "GGB": "ggb",
        "教学大纲": "syllabus",
        "理论卡片": "theory"
    }
    
    # 1. 构建查询文本
    query_texts = [query, core_theme]
    
    # 【V114.0强制优化】对于习题检索，如果LLM输出了多个主题（包含逗号），
    # 只保留第一个包含"的"的主题，因为包含"的"的主题更完整
    # 例如："分段函数单调性,分段函数" -> 只使用"分段函数单调性"
    if isinstance(core_theme, str) and ',' in core_theme:
        parts = [p.strip() for p in core_theme.split(',') if p.strip()]
        # 找到第一个包含"的"的主题（最完整的主题）
        first_with_de = None
        for part in parts:
            if '的' in part:
                first_with_de = part
                break
        
        if first_with_de:
            # 使用完整的主题替换原始主题
            core_theme = first_with_de
            query_texts = [query, core_theme]
            logger.info(f"[V114.0强制优化] LLM输出了多个主题，已强制使用完整主题: '{core_theme}'")
    
    # 【V65.2新增】如果是组合查询，添加拆分后的子主题进行检索，提高召回率
    # 【V112.0优化】对于习题检索，禁用主题拆分扩展
    # 只有当core_theme明确包含多个独立的知识点时（如"指数函数和对数函数"），才启用拆分
    enable_theme_split = False  # 默认禁用
    if isinstance(core_theme, str) and ',' in core_theme:
        # 检查是否应该拆分：如果主题之间是独立的（没有"的"等连接词），则拆分
        # 例如："指数函数和对数函数" -> 应该拆分
        # 例如："分段函数单调性" -> 不应该拆分
        parts = [p.strip() for p in core_theme.split(',') if p.strip()]
        # 如果所有部分都包含"的"，说明是复合主题，不拆分
        all_have_de = all('的' in p for p in parts)
        if not all_have_de and len(parts) > 1:
            enable_theme_split = True
        
        if enable_theme_split:
            query_texts.extend(parts)
            logger.info(f"[V65.2扩展查询] 原始查询: {query_texts[:2]}, 扩展后: {query_texts}")
    elif isinstance(core_theme, list):
        query_texts.extend(core_theme)
        logger.info(f"[V65.2扩展查询] 原始查询: {query_texts[:2]}, 扩展后: {query_texts}")
    
    # 2. 构建过滤条件
    where_filters = []
    
    # 资源类型过滤（转换为英文）
    if resource_types:
        mapped_types = []
        for rt in resource_types:
            mapped_types.append(resource_type_mapping.get(rt, rt))
        where_filters.append({"resource_type": {"$in": mapped_types}})
    
    # 难度过滤（使用原始字段）
    if difficulty:
        difficulty_map = {
            "简单": ["简单", "1", "2"],
            "中等": ["中等", "3"],
            "困难": ["困难", "4", "5"]
        }
        if difficulty in difficulty_map:
            where_filters.append({"难度": {"$in": difficulty_map[difficulty]}})
    
    # 题型过滤（使用分析字段）
    if question_type:
        where_filters.append({"analysis.题型": question_type})
    
    # 组合过滤条件
    where_clause = None
    if where_filters:
        if len(where_filters) == 1:
            where_clause = where_filters[0]
        else:
            where_clause = {"$and": where_filters}
    
    # 3. 获取对应板块集合
    collection_name = _get_collection_name_by_theme(core_theme)
    
    try:
        collection = vector_db.get_collection(collection_name)
    except Exception as e:
        logger.warning(f"集合 {collection_name} 不存在: {e}")
        try:
            collection = vector_db.get_collection("math_resources_general")
        except Exception as e2:
            logger.error(f"通用集合也不存在: {e2}")
            return []
    
    # 4. 执行向量检索
    try:
        results = collection.query(
            query_texts=query_texts,
            n_results=n_results * 10,  # 【V63.0改进】扩大候选池，从 *6 改为 *10，给后续过滤更多空间
            where=where_clause,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        logger.error(f"向量检索失败: {e}")
        return []
    
    # 【V106.0新增】知识点强制匹配 - 如果向量搜索没有返回足够的知识点匹配结果，直接查询包含目标知识点的文档
    if core_theme and isinstance(core_theme, str):
        results = _enhance_with_knowledge_point_matching(
            collection, core_theme, results, n_results, where_clause
        )
    
    # 5. 简单精排
    scored_results = []
    
    docs = results['documents'][0] if results.get('documents') else []
    metas = results['metadatas'][0] if results.get('metadatas') else []
    distances = results['distances'][0] if results.get('distances') else []
    
    for i, (doc, meta, distance) in enumerate(zip(docs, metas, distances)):
        score = 0.0
        analysis_json = meta.get('analysis_json', '')
        analysis = {}
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
            except:
                pass
        
        # ===== 1. 知识点匹配（analysis字段 + 原始知识点标签 合并去重）=====
        knowledge_points = list(analysis.get('知识点', []))
        # 补充原始知识点标签字段（两个字段名都检查）
        original_kp = meta.get('知识点标签', '') or meta.get('知识点', '')
        if original_kp:
            # 【V65.0改进】处理分号分隔的知识点标签，合并为完整表述
            original_kp_str = str(original_kp).replace('；', ';').strip()
            if ';' in original_kp_str:
                parts = [p.strip() for p in original_kp_str.split(';') if p.strip()]
                if len(parts) >= 2:
                    # 将第一个知识点作为主体，后续知识点用"的"连接
                    merged_kp = parts[0]
                    for part in parts[1:]:
                        merged_kp += f"的{part}"
                    if merged_kp and merged_kp not in knowledge_points:
                        knowledge_points.append(merged_kp)
                else:
                    kp = parts[0] if parts else ''
                    if kp and kp not in knowledge_points:
                        knowledge_points.append(kp)
            else:
                # 没有分号，直接添加
                kp = original_kp_str
                if kp and kp not in knowledge_points:
                    knowledge_points.append(kp)

        # 将 core_theme 拆分为独立子主题（兼容字符串逗号分隔和列表两种格式）
        if isinstance(core_theme, list):
            _theme_parts = core_theme
        elif isinstance(core_theme, str):
            _theme_parts = [p.strip() for p in core_theme.split(',') if p.strip()]
        else:
            _theme_parts = []

        # 同义词标准化
        _theme_parts_norm = []
        for _p in _theme_parts:
            _norm = _p.replace('图象', '图像')
            _theme_parts_norm.append(_norm)

        # 【V105.0优化】知识点精确匹配加分 - 只使用最核心的主题进行匹配，避免语义扩散
        # 例如：core_theme="分段函数单调性, 分段函数, 函数的单调性"，只使用"分段函数单调性"
        # 这样可以确保只有知识点完全匹配的习题才能获得高分，提高检索精准度
        exact_kp_bonus = 0.0
        
        if _theme_parts:
            # 只使用第一个（最核心的）主题进行匹配
            primary_theme = _theme_parts[0].strip()
            if primary_theme and len(primary_theme) >= 2:
                # 检查核心主题是否在知识点标签中（完全匹配或作为子串）
                if any(primary_theme == kp or primary_theme in kp for kp in knowledge_points):
                    exact_kp_bonus = 0.8  # 【V105.0】只对核心主题匹配给予高额加分
                    logger.info(f"[V105.0] 核心主题精确匹配: '{primary_theme}' in {knowledge_points}, +0.8")
        score += exact_kp_bonus

        # 用拆分后的子主题逐个匹配知识点
        _kp_matched = False
        for _part, _part_norm in zip(_theme_parts, _theme_parts_norm):
            if not _part:
                continue
            # 精确匹配（子主题或标准化版本在知识点列表中）
            if _part in knowledge_points or _part_norm in knowledge_points:
                score += 0.4  # 【V63.0改进】提高知识点匹配权重从0.3到0.4，确保知识点匹配的优先级更高
                _kp_matched = True
                break
            # 【V65.0改进】子主题包含在某个知识点中（支持合并后的知识点，如"函数单调性的区间判断"）
            if any(_part in kp or _part_norm in kp for kp in knowledge_points):
                score += 0.2  # 【V63.0改进】提高部分匹配权重从0.15到0.2
                _kp_matched = True
                break
            # 【V65.0新增】某个知识点包含在子主题中（反向匹配）
            if any(kp in _part or kp in _part_norm for kp in knowledge_points):
                score += 0.15  # 【V63.0改进】提高弱匹配权重从0.1到0.15
                _kp_matched = True
                break
            # 【V65.0新增】检查子主题的各个词是否都在知识点中（分词匹配）
            # 例如："函数的单调性" -> ["函数", "单调性"]，检查这些词是否都在知识点中
            part_words = [_w.strip() for _w in _part.replace('的', ' ').split() if _w.strip() and len(_w.strip()) > 1]
            if part_words:
                for kp in knowledge_points:
                    if all(word in kp for word in part_words):
                        score += 0.15  # 分词匹配成功
                        _kp_matched = True
                        break
                if _kp_matched:
                    break
        # 兼容旧逻辑：如果拆分失败，仍用原始 core_theme 匹配
        if not _kp_matched and core_theme:
            if core_theme in knowledge_points:
                score += 0.4
            elif any(core_theme in kp for kp in knowledge_points):
                score += 0.2
            elif any(kp in core_theme for kp in knowledge_points):
                score += 0.15
        
        # ===== 2. 核心考点匹配（改用拆分后的子主题逐个匹配）=====
        core_point = analysis.get('核心考点', '')
        if core_point:
            _cp_matched = False
            for _part, _part_norm in zip(_theme_parts, _theme_parts_norm):
                if not _part:
                    continue
                if _part in core_point or _part_norm in core_point:
                    score += 0.15
                    _cp_matched = True
                    break
                if core_point in _part or core_point in _part_norm:
                    score += 0.1
                    _cp_matched = True
                    break
            # 兼容旧逻辑
            if not _cp_matched and core_theme:
                if core_theme in core_point:
                    score += 0.15
                elif core_point in core_theme:
                    score += 0.1
        
        # ===== 3. 涉及公式匹配（改用拆分后的子主题逐个匹配）=====
        formulas = analysis.get('涉及公式', [])
        if isinstance(formulas, list):
            for formula in formulas:
                _matched = False
                for _part, _part_norm in zip(_theme_parts, _theme_parts_norm):
                    if not _part:
                        continue
                    if _part in formula or _part_norm in formula:
                        _matched = True
                        break
                if _matched:
                    score += 0.1
                    break
            else:
                # 兼容旧逻辑
                if core_theme:
                    for formula in formulas:
                        if core_theme in formula:
                            score += 0.1
                            break

        # ===== 4. 解题思路匹配（改用拆分后的子主题逐个匹配）=====
        solution_idea = analysis.get('解题思路', '')
        if solution_idea:
            _matched = False
            for _part, _part_norm in zip(_theme_parts, _theme_parts_norm):
                if not _part:
                    continue
                if _part in solution_idea or _part_norm in solution_idea:
                    _matched = True
                    break
            if _matched:
                score += 0.1
            else:
                # 兼容旧逻辑
                if core_theme and core_theme in solution_idea:
                    score += 0.1
        
        # ===== 5. 考察能力匹配 =====
        abilities = analysis.get('考察能力', [])
        if isinstance(abilities, list):
            for ability in abilities:
                if ability in ["数学建模", "实际应用", "应用"]:
                    if any(kw in query for kw in ["应用", "实际", "生活"]):
                        score += 0.08
                elif ability in ["逻辑推理", "推理"]:
                    if any(kw in query for kw in ["推理", "证明"]):
                        score += 0.05
                elif ability in ["空间想象", "画图"]:
                    if any(kw in query for kw in ["画图", "空间", "几何"]):
                        score += 0.08
        
        # ===== 6. 题目分类匹配 =====
        question_category = analysis.get('题目分类', '')
        if question_category:
            if "综合题" in question_category and any(kw in query for kw in ["综合", "综合题"]):
                score += 0.05
            elif "压轴题" in question_category and any(kw in query for kw in ["压轴", "难题"]):
                score += 0.05
        
        # ===== 7. 是否需要画图匹配 =====
        need_drawing = analysis.get('是否需要画图', False)
        if need_drawing and any(kw in query for kw in ["画图", "图形", "作图"]):
            score += 0.1
        
        # ===== 8. 原始知识点匹配（已在第1步合并，此处跳过，避免重复加分）=====
        
        # ===== 9. 距离评分（提高权重）=====
        score += max(0, (1 - distance / 1.2)) * 0.4
        
        # ===== 10. 文档内容匹配（兜底，改用拆分后的子主题逐个匹配）=====
        if doc:
            _matched = False
            for _part, _part_norm in zip(_theme_parts, _theme_parts_norm):
                if not _part:
                    continue
                if _part in doc or _part_norm in doc:
                    _matched = True
                    break
            if _matched:
                score += 0.1
            else:
                # 兼容旧逻辑
                if core_theme and core_theme in doc:
                    score += 0.1
        
        scored_results.append({
            'document': doc,
            'metadata': meta,
            'score': score,
            'distance': distance,
            # 【V65.3新增】添加顶层question字段，用于resource_identity去重
            'question': meta.get('题干', '').strip()
        })
    
    # 6. 过滤非习题资源和空内容资源
    # 在排序前先过滤，确保只保留有效的习题资源
    filtered_results = []
    valid_types = set(mapped_types) if 'mapped_types' in dir() else {'exercise'}
    
    for result in scored_results:
        meta = result['metadata']
        resource_type = meta.get('resource_type', '').lower()
        
        # 过滤非习题资源
        if resource_type not in valid_types:
            continue
        
        # 检查是否有有效内容（题干或图片）
        # 有些习题的完整题干以图片形式保存，题目文件名字段存储图片名
        question = meta.get('题干', '').strip()
        filename = meta.get('题目文件名', '').strip()
        
        # 至少有题干或图片才算有效习题
        if not question and not filename:
            continue
        
        filtered_results.append(result)
    
    # 7. 排序
    filtered_results.sort(key=lambda x: -x['score'])
    
    # 8. 去重优化：对于具体的知识点查询，允许同一个文件返回多道习题
    # 【V63.0改进】判断是否为具体的知识点查询
    is_specific_topic_query = False
    if core_theme and len(_theme_parts) <= 2:  # 查询主题比较具体（1-2个子主题）
        # 检查是否有明确的知识点关键词
        specific_keywords = [
            '函数', '指数', '对数', '三角', '幂', '二次', '一次', '概率', '统计', '几何', '代数',
            '线面角', '二面角', '空间角', '面面平行', '线面平行', '线线平行',
            '面面垂直', '线面垂直', '线线垂直', '向量', '棱柱', '棱锥', '圆柱', '圆锥', '球'
        ]
        if any(kw in core_theme for kw in specific_keywords):
            is_specific_topic_query = True
            logger.info(f"[V63.0去重优化] 检测到具体知识点查询: '{core_theme}'，允许同一文件返回多道习题")
    
    if is_specific_topic_query:
        # 对于具体知识点查询，不去重，允许同一文件的多道习题都被返回
        final_results = filtered_results[:n_results]
        logger.info(f"[V63.0去重优化] 不去重模式，返回 {len(final_results)} 条结果")
    else:
        # 对于宽泛查询，保持原有去重逻辑
        seen_files = set()
        final_results = []
        for result in filtered_results:
            source_file = result['metadata'].get('source_file', '')
            if source_file and source_file in seen_files:
                continue
            if source_file:
                seen_files.add(source_file)
            final_results.append(result)
            if len(final_results) >= n_results:
                break
        logger.info(f"[V63.0去重优化] 去重模式，返回 {len(final_results)} 条结果")
    
    logger.info(f"简化检索完成: 主题='{core_theme}', 返回={len(final_results)}条")
    
    # 【V65.2新增】为习题结果添加图片URL字段
    from app.core.retrieval.methods.process_exercise_resource import _ProcessExerciseResourceMixin
    
    logger.info(f"[V65.2图片调试] simple_exercise_retrieval: 开始处理 {len(final_results)} 条习题结果的图片URL")
    
    # 创建临时对象来调用图片URL解析方法
    class TempProcessor(_ProcessExerciseResourceMixin):
        def __init__(self):
            pass
    
    processor = TempProcessor()
    
    for idx, result in enumerate(final_results):
        metadata = result.get('metadata', {})
        if metadata:
            # 创建一个临时的resource字典
            temp_resource = {}
            try:
                processor._process_exercise_resource(temp_resource, metadata)
                
                # 将图片URL字段添加到result中
                result['question_image_url'] = temp_resource.get('question_image_url', '')
                result['answer_image_url'] = temp_resource.get('answer_image_url', '')
                result['has_question_image'] = temp_resource.get('has_question_image', False)
                result['has_answer_image'] = temp_resource.get('has_answer_image', False)
                result['question_format'] = temp_resource.get('question_format', 'text')
                result['answer_format'] = temp_resource.get('answer_format', 'text')
                
                # 【V65.2调试】记录图片URL信息
                title = metadata.get('title', '')
                filename = metadata.get('题目文件名', '')
                question_img = result.get('question_image_url', '')
                answer_img = result.get('answer_image_url', '')
                if filename or question_img or answer_img:
                    logger.info(f"[V65.2图片调试] [{idx+1}] 习题: {title}, 文件名: {filename}, 题目图片: {question_img[:80] if question_img else '无'}, 答案图片: {answer_img[:80] if answer_img else '无'}")
            except Exception as e:
                logger.error(f"[V65.2图片调试] 处理第{idx+1}条习题时出错: {e}")
    
    return final_results


def _get_collection_name_by_theme(core_theme):
    """根据主题获取集合名称（动态利用知识图谱）"""
    if not core_theme:
        return "math_resources_general"
    
    # 首先尝试使用知识图谱进行动态主题识别
    collection_name = _get_collection_by_knowledge_graph(core_theme)
    if collection_name:
        return collection_name
    
    # 如果知识图谱没有匹配，使用硬编码关键词作为备用
    statistics_keywords = ["概率", "统计", "抽样", "随机变量", "回归", "相关"]
    function_keywords = ["函数", "指数", "对数", "三角", "幂", "二次", "一次", "反函数"]
    algebra_keywords = ["代数", "复数", "虚数", "数系"]
    geometry_keywords = [
        "几何", "立体", "向量", "空间", "解析几何", "平面几何",
        "面面平行", "线面平行", "线线平行", 
        "面面垂直", "线面垂直", "线线垂直",
        "棱柱", "棱锥", "圆柱", "圆锥", "球",
        "正方体", "长方体", "表面积", "体积",
        "线面角", "二面角", "空间角", "夹角"
    ]
    
    if any(kw in core_theme for kw in statistics_keywords):
        return "math_resources_probability"
    elif any(kw in core_theme for kw in function_keywords):
        return "math_resources_function"
    elif any(kw in core_theme for kw in algebra_keywords):
        return "math_resources_algebra"
    elif any(kw in core_theme for kw in geometry_keywords):
        return "math_resources_geometry"
    
    return "math_resources_general"


def _get_collection_by_knowledge_graph(core_theme):
    """利用知识图谱动态识别主题所属的集合"""
    try:
        from app.core.knowledge_graph import KnowledgeGraph
        
        kg = KnowledgeGraph()
        
        # 使用知识图谱的 universal_match 方法匹配主题
        match_result = kg.universal_match([core_theme])
        
        if match_result['matched_nodes']:
            # 获取匹配节点的标签和关键词
            labels = match_result['labels']
            keywords = match_result['keywords']
            all_text = ' '.join(labels + keywords)
            
            # 定义集合类型及其关键词模式（更宽松的匹配）
            collection_patterns = {
                '概率统计': ['概率', '统计', '随机', '抽样', '回归', '期望', '方差'],
                '函数': ['函数', '三角', '指数', '对数', '幂', '周期', '单调'],
                '代数': ['代数', '复数', '虚数', '数系', '方程', '不等式'],
                '几何': ['几何', '立体', '空间', '向量', '平行', '垂直', 
                         '角', '面', '线', '棱柱', '棱锥', '圆锥', '曲线']
            }
            
            # 统计每个集合类型的匹配分数
            scores = {}
            for collection_type, patterns in collection_patterns.items():
                score = sum(1 for pattern in patterns if pattern in all_text)
                scores[collection_type] = score
            
            # 选择分数最高的集合类型（必须至少有一个匹配）
            max_score = max(scores.values())
            if max_score > 0:
                for collection_type, score in scores.items():
                    if score == max_score:
                        collection_name_map = {
                            '概率统计': 'math_resources_probability',
                            '函数': 'math_resources_function',
                            '代数': 'math_resources_algebra',
                            '几何': 'math_resources_geometry'
                        }
                        logger.info(f"[动态主题识别] 通过知识图谱识别'{core_theme}'属于'{collection_type}'板块 (匹配分数: {score})")
                        return collection_name_map[collection_type]
            
            # 如果匹配到节点但无法确定类型，检查节点的父节点
            for node in match_result['matched_nodes']:
                parent_id = node.get('parent')
                if parent_id and hasattr(kg, '_node_id_index'):
                    parent_node = kg._node_id_index.get(parent_id)
                    if parent_node:
                        parent_label = parent_node.get('label', '')
                        for collection_type, patterns in collection_patterns.items():
                            if any(pattern in parent_label for pattern in patterns):
                                collection_name_map = {
                                    '概率统计': 'math_resources_probability',
                                    '函数': 'math_resources_function',
                                    '代数': 'math_resources_algebra',
                                    '几何': 'math_resources_geometry'
                                }
                                logger.info(f"[动态主题识别] 通过父节点'{parent_label}'识别'{core_theme}'属于'{collection_type}'板块")
                                return collection_name_map[collection_type]
        
    except Exception as e:
        logger.warning(f"[动态主题识别] 知识图谱识别失败，使用备用方案: {e}")
    
    return None


def _enhance_with_knowledge_point_matching(collection, core_theme, results, n_results, where_clause):
    """
    【V106.0新增】知识点强制匹配 - 确保包含目标知识点的文档被优先返回
    
    Args:
        collection: ChromaDB集合
        core_theme: 核心主题
        results: 向量搜索结果
        n_results: 期望返回数量
        where_clause: 过滤条件
    
    Returns:
        增强后的检索结果
    """
    try:
        # 检查向量搜索结果中是否有足够的知识点匹配
        docs = results['documents'][0] if results.get('documents') else []
        metas = results['metadatas'][0] if results.get('metadatas') else []
        distances = results['distances'][0] if results.get('distances') else []
        
        kp_matched_count = 0
        for meta in metas[:n_results]:
            analysis_json = meta.get('analysis_json', '')
            if analysis_json:
                try:
                    import json
                    analysis = json.loads(analysis_json)
                    knowledge_points = analysis.get('知识点', [])
                    if isinstance(knowledge_points, list):
                        if any(core_theme in kp for kp in knowledge_points):
                            kp_matched_count += 1
                except:
                    pass
        
        # 如果前n_results条结果中知识点匹配的数量少于30%，则强制补充
        if kp_matched_count < max(1, int(n_results * 0.3)):
            logger.info(f"[V106.0] 知识点匹配不足({kp_matched_count}/{n_results})，强制补充包含'{core_theme}'知识点的文档")
            
            # 获取所有文档（带过滤条件）
            all_docs = collection.get(
                where=where_clause,
                limit=200,
                include=["documents", "metadatas"]
            )
            
            all_docs_list = all_docs['documents'] if all_docs.get('documents') else []
            all_metas_list = all_docs['metadatas'] if all_docs.get('metadatas') else []
            
            # 筛选出包含目标知识点的文档
            kp_matched_docs = []
            kp_matched_metas = []
            
            seen_ids = set()
            for existing_meta in metas:
                if 'id' in existing_meta:
                    seen_ids.add(existing_meta['id'])
            
            for doc, meta in zip(all_docs_list, all_metas_list):
                # 跳过已存在的文档
                if 'id' in meta and meta['id'] in seen_ids:
                    continue
                
                analysis_json = meta.get('analysis_json', '')
                if analysis_json:
                    try:
                        import json
                        analysis = json.loads(analysis_json)
                        knowledge_points = analysis.get('知识点', [])
                        if isinstance(knowledge_points, list):
                            if any(core_theme in kp for kp in knowledge_points):
                                kp_matched_docs.append(doc)
                                kp_matched_metas.append(meta)
                    except:
                        pass
            
            logger.info(f"[V106.0] 找到 {len(kp_matched_docs)} 条包含'{core_theme}'知识点的文档")
            
            # 将知识点匹配的文档插入到结果前面
            if kp_matched_docs:
                # 限制补充数量
                max_add = n_results - kp_matched_count
                docs = kp_matched_docs[:max_add] + docs
                metas = kp_matched_metas[:max_add] + metas
                distances = [0.1] * min(max_add, len(kp_matched_docs)) + distances
            
            # 重建结果结构
            results = {
                'documents': [docs],
                'metadatas': [metas],
                'distances': [distances]
            }
        
        return results
    
    except Exception as e:
        logger.warning(f"[V106.0] 知识点强制匹配失败，使用原始结果: {e}")
        return results