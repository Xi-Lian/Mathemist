"""
资源检索模块

职责：
- 使用ChromaDB进行语义检索
- 根据查询和意图检索相关资源
- 对检索结果进行分类和组织
- 实现习题资源的特殊处理逻辑
- V33.0改进：支持数量限制、年级筛选、主题澄清

依赖：
- model_config (模型配置)
- resource_classifier (资源分类)
- vector_database_builder (向量数据库构建)
- resource_table_parser (资源汇总表解析)
- chromadb (向量数据库)
- sentence_transformers (Embedding模型)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config
from .resource_classifier import ResourceClassifier
from .vector_database_builder import VectorDatabaseBuilder
from .resource_table_parser import ResourceTableParser
from .theme_matcher import get_theme_matcher
from .theme_matcher_v90 import get_theme_matcher_v90
from .content_feature_extractor import get_content_feature_extractor
from ..config.resource_type_config import (
    get_db_type,
    get_resource_type_mapping,
    get_standard_name,
    get_all_user_types,
    get_all_db_types
)
from ..config.dynamic_config_loader import get_config_loader


class ResourceRetriever:
    """资源检索器"""
    
    COLLECTION_NAME = "math_resources"
    DEFAULT_N_RESULTS = 500
    
    def __init__(self, learning_resource_path: str = None):
        """
        初始化资源检索器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        self.model_config = model_config
        
        if learning_resource_path is None:
            current_dir = Path(__file__).parent.parent.parent
            learning_resource_path = current_dir / 'learning_resource'
        
        self.learning_resource_path = Path(learning_resource_path).resolve()
        
        self.vector_db_builder = VectorDatabaseBuilder(str(self.learning_resource_path))
        self.parser = ResourceTableParser(str(self.learning_resource_path))
        
        self.content_extractor = get_content_feature_extractor()
        
        from .grade_metadata_enricher import get_grade_enricher
        self.grade_enricher = get_grade_enricher()
        
        from .content_feature_extractor import SubjectiveIntentInterpreter
        self.subjective_interpreter = SubjectiveIntentInterpreter()
        
        # 初始化主题匹配器
        self.theme_matcher = get_theme_matcher()
        
        # V60.0改进：使用动态配置加载器，从配置文件加载知识点层级结构
        # 这样当资源库扩展时，只需更新配置文件，无需修改代码
        self.config_loader = get_config_loader()
        self.knowledge_hierarchy = self.config_loader.get_knowledge_hierarchy()
        
        # V60.0改进：从配置文件加载意图模式
        self.query_intent_patterns = self.config_loader.get_intent_patterns()
        
        # V53.1改进：动态生成相关主题列表，基于knowledge_hierarchy
        # 不再硬编码具体主题，而是从knowledge_hierarchy中提取所有主题
        self.all_themes = self.config_loader.get_all_themes()
        
        # V60.0改进：使用配置加载器动态获取函数相关主题
        # 通过parent_topic判断，而不是硬编码关键词
        self.function_related_themes = self.config_loader.get_function_related_themes()
        
        # V53.1改进：动态生成所有主题的关键词列表
        # 用于年级匹配等场景，避免硬编码
        self.all_theme_keywords = self.config_loader.get_all_keywords()
    
    # V51.0改进：动态查询意图识别方法
    def _detect_query_intents(self, query: str) -> List[Dict[str, Any]]:
        """
        动态识别查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            识别到的意图列表，按优先级排序
        """
        detected_intents = []
        query_lower = query.lower()
        
        for intent_name, intent_config in self.query_intent_patterns.items():
            # 检查是否匹配任何模式
            matched_patterns = []
            for pattern in intent_config["patterns"]:
                if pattern in query:
                    matched_patterns.append(pattern)
            
            if matched_patterns:
                detected_intents.append({
                    "name": intent_name,
                    "priority": intent_config["priority"],
                    "matched_patterns": matched_patterns,
                    "keywords": intent_config["keywords"],
                    "resource_indicators": intent_config["resource_indicators"]
                })
        
        # 按优先级排序（高优先级在前）
        detected_intents.sort(key=lambda x: x["priority"], reverse=True)
        
        return detected_intents
    
    # V51.0改进：动态生成增强查询
    def _enhance_query_dynamically(self, query: str, detected_intents: List[Dict[str, Any]]) -> str:
        """
        根据检测到的意图动态增强查询
        
        Args:
            query: 原始查询
            detected_intents: 检测到的意图列表
            
        Returns:
            增强后的查询
        """
        if not detected_intents:
            # V52.0改进：即使没有检测到意图，也进行基础增强
            return self._basic_query_enhancement(query)
        
        enhanced_parts = [query]
        added_keywords = set()
        
        # 根据优先级添加关键词
        for intent in detected_intents:
            for keyword in intent["keywords"]:
                if keyword not in added_keywords and keyword not in query:
                    enhanced_parts.append(keyword)
                    added_keywords.add(keyword)
        
        enhanced_query = " ".join(enhanced_parts)
        
        # V52.0改进：添加基础增强
        enhanced_query = self._basic_query_enhancement(enhanced_query)
        
        print(f"   🔍 V51.0动态查询增强: '{query}' -> '{enhanced_query}'")
        print(f"   🔍 V51.0检测到的意图: {[i['name'] for i in detected_intents]}")
        
        return enhanced_query
    
    # V52.0改进：基础查询增强
    def _basic_query_enhancement(self, query: str) -> str:
        """
        基础查询增强，处理常见的查询模式
        
        Args:
            query: 原始查询
            
        Returns:
            增强后的查询
        """
        enhanced_query = query
        
        # V52.0改进：将"例子"转换为"习题"
        if "例子" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '例子' -> '习题'")
        
        # V52.0改进：将"实例"转换为"习题"
        if "实例" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '实例' -> '习题'")
        
        # V52.0改进：将"案例"转换为"习题"
        if "案例" in query and "习题" not in query:
            enhanced_query = enhanced_query + " 习题"
            print(f"   🔍 V52.0基础增强: '案例' -> '习题'")
        
        # V52.0改进：将"生活中应用"转换为"应用题"
        if "生活中应用" in query or "在生活中应用" in query:
            if "应用题" not in query:
                enhanced_query = enhanced_query + " 应用题"
                print(f"   🔍 V52.0基础增强: '生活中应用' -> '应用题'")
        
        # V52.0改进：将"实际应用"转换为"应用题"
        if "实际应用" in query and "应用题" not in query:
            enhanced_query = enhanced_query + " 应用题"
            print(f"   🔍 V52.0基础增强: '实际应用' -> '应用题'")
        
        # V52.0改进：将"实际问题的应用"转换为"应用题"
        if "实际问题的应用" in query or "实际问题的应用题" in query:
            if "应用题" not in query:
                enhanced_query = enhanced_query + " 应用题"
                print(f"   🔍 V52.0基础增强: '实际问题的应用' -> '应用题'")
        
        return enhanced_query
    
    # V51.0改进：动态调整检索数量
    def _adjust_retrieval_count(self, query: str, detected_intents: List[Dict[str, Any]], base_count: int, resource_types: List[str] = None) -> int:
        """
        根据检测到的意图动态调整检索数量
        
        Args:
            query: 用户查询
            detected_intents: 检测到的意图列表
            base_count: 基础检索数量
            
        Returns:
            调整后的检索数量
        """
        adjusted_count = base_count
        
        # 根据意图优先级调整数量
        if detected_intents:
            max_priority = max(i["priority"] for i in detected_intents)
            
            # V90.2修复：对于课件查询，使用更低的检索数量
            is_courseware_query = any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types))
            
            # 高优先级意图增加检索数量
            if max_priority >= 10:  # 证明题、应用题等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件高优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 700)
                    print(f"   🔍 V51.0高优先级意图: 增加检索数量到 {adjusted_count}")
            elif max_priority >= 9:  # 单调性、奇偶性等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件中等优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 600)
                    print(f"   🔍 V51.0中等优先级意图: 增加检索数量到 {adjusted_count}")
            elif max_priority >= 8:  # 难度、年级等
                if is_courseware_query:
                    adjusted_count = max(base_count, 200)  # V90.2修复：课件查询使用200
                    print(f"   🔍 V90.2课件普通优先级意图: 使用检索数量 {adjusted_count}")
                else:
                    adjusted_count = max(base_count, 500)
                    print(f"   🔍 V51.0普通优先级意图: 增加检索数量到 {adjusted_count}")
        
        # 特殊处理：应用题和生活应用查询
        has_application_intent = any(i["name"] in ["application_problem", "trig_application", "quadratic_application"] for i in detected_intents)
        if has_application_intent:
            adjusted_count = max(adjusted_count, 800)
            print(f"   🔍 V51.0应用题查询: 进一步增加检索数量到 {adjusted_count}")
        
        # 特殊处理：组合查询（多个高优先级意图）
        high_priority_intents = [i for i in detected_intents if i["priority"] >= 9]
        # V90.1修复：对于课件查询，不要使用过高的检索数量
        is_courseware_query = any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types))
        if len(high_priority_intents) >= 2 and not is_courseware_query:
            adjusted_count = max(adjusted_count, 900)
            print(f"   🔍 V51.0组合查询: 进一步增加检索数量到 {adjusted_count}")
        elif len(high_priority_intents) >= 2 and is_courseware_query:
            # 对于课件查询，使用较低的检索数量
            # V90.2修复：进一步降低课件检索数量，避免ChromaDB错误
            adjusted_count = max(adjusted_count, 200)
            print(f"   🔍 V90.2课件组合查询: 使用检索数量 {adjusted_count}")
        
        # V54.0改进：对于教案/课件/教学大纲等非习题资源的查询，增加检索数量
        # 因为这些资源在向量空间中的分布与习题资源不同，需要检索更多结果才能找到相关资源
        non_exercise_keywords = ['教案', '课件', '教学大纲', '课例', '教学设计']
        print(f"   🔍 V54.0调试 - 查询: {query}, non_exercise_keywords: {non_exercise_keywords}, resource_types: {resource_types}")
        
        # V67.0改进：检查resource_types参数，而不仅仅是查询文本
        is_non_exercise_query = False
        if any(keyword in query for keyword in non_exercise_keywords):
            is_non_exercise_query = True
        elif resource_types:
            # 检查resource_types中是否包含非习题资源类型
            non_exercise_types = ['教案', '课件', '教学大纲', '课例', '教学设计', 'GGB', 'GeoGebra']
            if any(rt in non_exercise_types for rt in resource_types):
                is_non_exercise_query = True
        
        if is_non_exercise_query:
            # V70.0改进：进一步增加非习题资源的检索数量
            # V75.0改进：对于课件资源，使用更高的检索数量
            # V90.0修复：修复ChromaDB错误，将课件检索数量降低到合理范围
            # V90.1修复：进一步降低课件检索数量，避免ChromaDB错误
            if any(kw in query for kw in ['课件', 'PPT', '幻灯片']) or (resource_types and any(rt in ['课件', 'PPT', '幻灯片'] for rt in resource_types)):
                adjusted_count = max(adjusted_count, 300)  # V90.1修复：将课件检索数量进一步降低到300
                print(f"   🔍 V90.1课件资源查询: 使用检索数量 {adjusted_count}")
            else:
                adjusted_count = max(adjusted_count, 500)  # V90.0修复：将其他非习题资源检索数量降低到500
                print(f"   🔍 V54.0非习题资源查询: 增加检索数量到 {adjusted_count}")
        else:
            print(f"   🔍 V54.0调试 - 查询不包含非习题关键词，不增加检索数量")
        
        return adjusted_count
    
    def retrieve(
        self, 
        query: str, 
        intent: str = "search", 
        n_results: int = None, 
        resource_types: List[str] = None,
        quantity_limit: Optional[int] = None,
        grade_info: Optional[Dict[str, Any]] = None,
        clarified_topic: Optional[Dict[str, Any]] = None,
        difficulty_info: Optional[Dict[str, Any]] = None
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
            print(f" 资源检索开始")
            print(f"📝 查询: {query}")
            print(f"🎯 意图: {intent}")
            print(f"📋 资源类型: {resource_types}")
            print(f"📋 V33.0数量限制: {quantity_limit}")
            print(f"📋 V33.0年级信息: {grade_info}")
            print(f"📋 V33.0主题澄清: {clarified_topic}")
            print(f"📋 V33.0难度信息: {difficulty_info}")
            
            # V61.0改进：如果外部没有传递resource_types，从查询中自动识别
            if not resource_types:
                resource_types = self._extract_resource_types_from_query(query)
                if resource_types:
                    print(f"📋 V61.0自动识别资源类型: {resource_types}")
            
            # V92.0改进：检查资源类型是否有效，只有6种资源类型
            if resource_types:
                from ..config.resource_type_config import is_valid_resource_type, get_supported_resource_types
                invalid_types = [rt for rt in resource_types if not is_valid_resource_type(rt)]
                if invalid_types:
                    print(f"⚠️ V92.0检测到无效资源类型: {invalid_types}")
                    print(f"📋 V92.0支持的资源类型: {[rt['name'] for rt in get_supported_resource_types()]}")
                    # 过滤掉无效的资源类型
                    resource_types = [rt for rt in resource_types if is_valid_resource_type(rt)]
                    if not resource_types:
                        print(f"❌ V92.0没有有效的资源类型，返回空结果")
                        return {
                            "exercise_resources": [],
                            "courseware_resources": [],
                            "lesson_plan_patterns": [],
                            "lesson_case_resources": [],
                            "ggb_resources": [],
                            "syllabus_resources": []
                        }
                    else:
                        print(f"✅ V92.0过滤后的资源类型: {resource_types}")
            
            # V33.0改进：处理"还要多一点"的逻辑
            if '还要多一点' in query or '再要一点' in query or '多一点' in query:
                # 对于"还要一点"的查询，应该基于之前的查询上下文
                # 这里简化处理，使用更宽松的阈值和更多的结果
                print(f"🔍 V33.0检测到'还要一点'查询，使用宽松模式")
                # 暂时将数量限制翻倍，以获取更多结果
                if quantity_limit:
                    quantity_limit = quantity_limit * 2
                # 使用更宽松的相似度阈值（在后续处理中）
                self._loose_mode = True
            else:
                self._loose_mode = False
            
            query_features = self.content_extractor.extract_query_content_features(query)
            self._current_query_features = query_features
            self._current_quantity_limit = quantity_limit
            self._current_grade_info = grade_info
            self._current_clarified_topic = clarified_topic
            self._current_difficulty_info = difficulty_info
            
            if query_features['has_content_requirement']:
                print(f"🔍 V9.1检测到内容查询要求:")
                print(f"   - 教学方法: {query_features['required_methods']}")
                print(f"   - 教学环节: {query_features['required_stages']}")
                print(f"   - 教学手段: {query_features['required_tools']}")
            
            if grade_info:
                print(f"🎓 V33.0年级信息（来自意图分析）: {grade_info}")
            else:
                fallback_grade = self.grade_enricher.extract_grade_from_query(query)
                if fallback_grade:
                    print(f"🎓 V33.0年级解析（回退）: {fallback_grade}")
                    self._current_grade_info = fallback_grade
                else:
                    print(f"🎓 V33.0年级解析: 未检测到年级信息")
            
            subjective_intent = self.subjective_interpreter.interpret(query)
            if subjective_intent:
                print(f"💭 V28.0主观意图解析:")
                print(f"   - 主观词汇: {subjective_intent.get('subjective_words', [])}")
                print(f"   - 难度范围: {subjective_intent.get('difficulty_range', None)}")
                print(f"   - 认知层次: {subjective_intent.get('cognitive_level', [])}")
                print(f"   - 用户场景: {subjective_intent.get('user_scenario', None)}")
                self._current_subjective_intent = subjective_intent
            else:
                print(f"💭 V28.0主观意图解析: 未检测到主观意图")
                self._current_subjective_intent = None
            
            if not self._check_vector_db_exists():
                print("⚠️  向量数据库不存在，尝试构建...")
                if not self.vector_db_builder.build_vector_database():
                    print("❌ 向量数据库构建失败")
                    return self._get_empty_result()
            
            client = self.vector_db_builder.get_chroma_client()
            embedding_model = self.vector_db_builder.get_embedding_model()
            
            # 获取集合
            collection = client.get_collection(name=self.COLLECTION_NAME)
            
            # V49.0改进：提取多维度查询条件
            print(f"\n🔍 V49.0开始提取多维度查询条件...")
            query_conditions = self._extract_query_conditions(query)
            
            # 从条件中获取核心主题
            # V68.0改进：首先从query_conditions中获取核心主题
            core_themes = query_conditions['knowledge_points']
            core_theme = ','.join(core_themes) if core_themes else ''
            print(f"🧠 识别核心主题: {core_theme}")
            
            # V68.0改进：如果core_theme为空，使用_extract_core_theme函数提取核心主题
            if not core_theme:
                core_theme = self._extract_core_theme(query)
                print(f"   📝 V68.0使用_extract_core_theme提取核心主题: '{core_theme}'")
                # 更新core_themes
                core_themes = [t.strip() for t in core_theme.split(',') if t.strip()]
            
            # V53.4改进：如果识别到的主题在knowledge_hierarchy中，但不是函数相关的主题，直接返回空结果
            # 这样可以确保当资源库只有函数板块时，查询其他知识板块会正确返回未找到资源
            if core_theme:
                theme_list = [t.strip() for t in core_theme.split(',') if t.strip()]
                all_non_function_themes = [
                    "立体几何", "空间点线面", "空间几何体", 
                    "概率", "统计", "概率与统计",
                    "数列", "不等式", "圆锥曲线", "导数", "向量", "立体几何初步", "空间向量"
                ]
                
                # 函数相关的主题名称
                function_related_theme_names = [
                    "二次函数", "指数函数", "对数函数", "三角函数", "幂函数", "一次函数",
                    "函数的概念", "函数应用", "二次函数应用", "三角函数应用", "幂函数应用",
                    "指数与对数函数综合", "函数的零点", "二分法", "函数的单调性", "函数的奇偶性", "函数的周期性",
                    "对数函数运算", "诱导公式", "三角恒等变换"
                ]
                
                # 检查是否有任何非函数主题
                has_non_function_theme = False
                for theme in theme_list:
                    if theme in all_non_function_themes:
                        has_non_function_theme = True
                        break
                    # 检查主题是否在knowledge_hierarchy中但不是函数相关主题
                    if theme in self.knowledge_hierarchy and theme not in function_related_theme_names:
                        has_non_function_theme = True
                        break
                    # 检查查询中是否包含明确的非函数板块关键词
                    # V93.0改进：导数是函数的重要组成部分，不应该被排除
                    query_lower = query.lower()
                    non_function_keywords = [
                        "立体几何", "空间几何", "空间向量",
                        "概率", "统计", "概率统计",
                        "数列", "等差数列", "等比数列",
                        "不等式", "线性规划",
                        "圆锥曲线", "椭圆", "双曲线", "抛物线"
                        # 注意：导数、微积分属于函数板块，不应该被排除
                    ]
                    if any(keyword in query_lower for keyword in non_function_keywords):
                        has_non_function_theme = True
                        break
                
                if has_non_function_theme:
                    print(f"⚠️ V53.4检测到非函数主题查询，直接返回空结果（资源库只有函数板块）")
                    return self._get_empty_result()
            
            # 从条件中获取其他维度
            question_type = query_conditions['question_type']
            difficulty = query_conditions['difficulty']
            grade = query_conditions['grade']
            exam_form = query_conditions['exam_form']
            quantity = query_conditions['quantity']
            
            # 如果用户指定了数量，使用用户指定的数量
            if quantity > 0:
                quantity_limit = quantity
                print(f"📝 V49.0使用用户指定的数量: {quantity}")
            
            # 提取题目类型
            if question_type:
                print(f"📝 提取到题目类型: {question_type}")
            
            # 提取难度
            if difficulty:
                print(f"📝 提取到难度: {difficulty}")
            
            # 提取年级
            if grade:
                print(f"📝 提取到年级: {grade}")
            
            # 提取考查形式
            if exam_form:
                print(f"📝 提取到考查形式: {exam_form}")
            
            # V15.1改进: 多主题分别检索策略
            # 当查询包含具体知识点时，优先使用最具体的主题进行检索
            if len(core_themes) > 1:
                print(f"🔄 检测到多个主题({len(core_themes)}个)，采用分别检索策略: {core_themes}")
                
                # V52.0改进：对于包含"应用"的主题，使用基础主题名称进行检索
                # 例如："幂函数的应用" -> "幂函数"，"函数的应用" -> "函数"
                # 但不要过度简化，避免"函数的应用" -> "函数"被过滤掉
                themes_to_search = []
                for theme in core_themes:
                    if "的应用" in theme and theme != "函数的应用":
                        # 提取基础主题名称
                        base_theme = theme.replace("的应用", "")
                        themes_to_search.append(base_theme)
                        print(f"   📝 V52.0简化主题: '{theme}' -> '{base_theme}'")
                    else:
                        themes_to_search.append(theme)
                
                print(f"   📝 V52.0使用简化主题进行检索: {themes_to_search}")
                
                # V15.1: 识别最具体的主题（包含具体知识点的主题）
                specific_themes = []
                generic_themes_list = []
                
                for theme in themes_to_search:
                    # 检查是否是通用主题
                    is_generic = theme in ["函数", "数学", "教学"]
                    if is_generic:
                        generic_themes_list.append(theme)
                    else:
                        specific_themes.append(theme)
                
                # V15.1: 优先检索具体主题，但保留通用主题作为补充
                if specific_themes:
                    print(f"   📝 V15.1优先检索具体主题: {specific_themes}")
                    if generic_themes_list:
                        print(f"   📝 V15.1保留通用主题作为补充: {generic_themes_list}")
                    themes_to_search = themes_to_search  # 仍然检索所有主题，但会在后续过滤
                else:
                    themes_to_search = themes_to_search
                
                all_results = []
                
                # V51.0改进：使用动态意图识别系统
                detected_intents = self._detect_query_intents(query)
                
                # 构建资源类型过滤条件
                resource_type_filters = []
                where_filter = None  # V55.1修复：初始化where_filter变量
                print(f"   🔍 调试 - 资源类型: {resource_types}")
                if resource_types and not any(rt in ["资料", "资源", "教学资源", "教学资料"] for rt in resource_types):
                    # 检查是否是教案、教学大纲等需要特殊处理的资源类型
                    special_resource_types = ["教案", "教学设计", "教学方案", "教学大纲", "大纲", "课程标准", "课件", "PPT", "幻灯片", "课例", "教学视频", "课堂实录", "GGB", "GeoGebra", "动态图", "可视化"]
                    
                    # 收集所有映射的数据库类型
                    db_types = []
                    for user_type in resource_types:
                        mapped_db_type = get_db_type(user_type)
                        print(f"   🔍 调试 - 资源类型映射: {user_type} -> {mapped_db_type}")
                        if mapped_db_type:
                            db_types.append(mapped_db_type)
                    
                    print(f"   🔍 调试 - 数据库类型: {db_types}")
                    if db_types:
                        # 对于多个资源类型，为每种类型创建单独的过滤条件
                        print(f"   📋 V54.0组合资源查询: 为每种资源类型单独检索")
                        print(f"   🔍 V56.4调试 - 为每种资源类型创建过滤条件: {db_types}")
                        print(f"   🔍 V54.0调试 - db_types: {db_types}")
                        for db_type in db_types:
                            resource_type_filters.append({"resource_type": db_type})
                            print(f"   🔍 V54.0调试 - 添加资源类型过滤: {db_type}")
                    else:
                        print(f"   ⚠️ V54.0调试 - db_types为空，无法创建资源类型过滤条件")
                # V46.1改进：对于单调性证明题查询，强制添加exercise过滤
                elif question_type == '证明题' and ('单调性' in query or '单调' in query):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V46.1单调性证明题：强制添加exercise过滤")
                # V48.0改进：对于函数选择题查询，强制添加exercise过滤
                elif question_type == '选择题' and ('函数' in query or '二次函数' in query or '三角函数' in query):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V48.0函数选择题：强制添加exercise过滤")
                # V52.0改进：对于习题、题目、练习题、例子、应用题查询，强制添加exercise过滤
                # 注意：只在用户明确要求习题资源时才添加过滤，避免影响教案、教学大纲等其他资源类型的查询
                # 只有当resource_type_filters为空时才执行这个过滤
                elif not resource_type_filters and any(kw in query for kw in ['习题', '题目', '练习题', '例子', '实例', '案例', '应用题', '实际应用', '生活应用']) and not any(kw in query for kw in ['教案', '教学设计', '教学方案', '教学大纲', '大纲', '课程标准', '课件', 'PPT', '幻灯片', '课例', '教学视频', '课堂实录', 'GGB', 'GeoGebra', '动态图', '可视化']):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V52.0习题查询：强制添加exercise过滤")
                
                # 执行检索
                if resource_type_filters:
                    # 对于组合资源查询，为每种资源类型单独执行检索
                    print(f"   🔍 开始执行组合资源查询，资源类型: {[rf['resource_type'] for rf in resource_type_filters]}")
                    # 先处理课件资源
                    for resource_filter in resource_type_filters:
                        if resource_filter['resource_type'] == 'courseware':
                            resource_type = resource_filter['resource_type']
                            print(f"\n  🔍 为资源类型 '{resource_type}' 执行检索...")
                            # 为课件资源设置合适的检索数量
                            n_results_per_theme = n_results or self.DEFAULT_N_RESULTS
                            # V51.0改进：动态调整检索数量
                            n_results_per_theme = self._adjust_retrieval_count(query, detected_intents, n_results_per_theme)
                            # V76.0改进：对于课件资源，不限制检索数量
                            print(f"   🔍 课件资源检索: 检索数量 {n_results_per_theme}")
                            
                            # 对于课件资源，使用原始查询而不是主题作为查询，以提高检索效果
                            query_text = query
                            print(f"   🔍 使用查询文本: '{query_text}' (资源类型: {resource_type})")
                            
                            # 使用ChromaDB的query方法
                            print(f"     🔍 执行ChromaDB查询: resource_type={resource_filter['resource_type']}, n_results={n_results_per_theme}")
                            theme_results = collection.query(
                                query_texts=[query_text],
                                n_results=n_results_per_theme,
                                where=resource_filter,
                                include=["documents", "metadatas", "distances"]
                            )
                            
                            # 调整结果格式以匹配后续处理
                            if theme_results.get("documents") and theme_results["documents"][0]:
                                theme_results["ids"] = [[f"courseware_{i}" for i in range(len(theme_results["documents"][0]))]]
                                print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条课件资源结果")
                                # 打印前3条课件资源的标题
                                for i in range(min(3, len(theme_results['documents'][0]))):
                                    meta = theme_results['metadatas'][0][i]
                                    title = meta.get('title', '未知')
                                    print(f"       - 课件资源{i+1}: {title}")
                                all_results.append(("课件", theme_results))
                            else:
                                print(f"     ❌ 未找到课件资源结果")
                                # 即使没有结果，也添加到all_results中，以确保后续处理能正确识别资源类型
                                theme_results["ids"] = [["courseware_0"]]
                                all_results.append(("课件", theme_results))
                    
                    # 处理其他资源类型（如习题）
                    for resource_filter in resource_type_filters:
                        if resource_filter['resource_type'] != 'courseware':
                            resource_type = resource_filter['resource_type']
                            for theme in themes_to_search:
                                print(f"\n  🔍 为主题 '{theme}' 执行检索 (资源类型: {resource_type})...")
                                
                                # 构建查询参数
                                n_results_per_theme = n_results or self.DEFAULT_N_RESULTS
                                
                                # V51.0改进：动态调整检索数量
                                n_results_per_theme = self._adjust_retrieval_count(query, detected_intents, n_results_per_theme)
                                
                                # V52.0改进：多主题查询增加检索数量，但不超过合理范围
                                if len(themes_to_search) > 1:
                                    n_results_per_theme = min(max(n_results_per_theme, 500), 700)
                                    print(f"   🔍 V52.0多主题查询: 增加检索数量到 {n_results_per_theme}")
                                
                                # 针对函数性质主题（单调性、奇偶性、周期性）增加检索数量，但不超过合理范围
                                if any(prop in theme for prop in ["函数的单调性", "函数的奇偶性", "函数的周期性"]):
                                    n_results_per_theme = min(max(n_results_per_theme, 600), 800)
                                    print(f"   🔍 函数性质查询: 增加检索数量到 {n_results_per_theme}")
                                
                                # 使用主题作为查询
                                query_text = theme
                                print(f"   🔍 使用查询文本: '{query_text}' (资源类型: {resource_type})")
                                
                                # 使用ChromaDB的query方法
                                print(f"     🔍 执行ChromaDB查询: resource_type={resource_type}, n_results={n_results_per_theme}")
                                theme_results = collection.query(
                                    query_texts=[query_text],
                                    n_results=n_results_per_theme,
                                    where=resource_filter,
                                    include=["documents", "metadatas", "distances"]
                                )
                                
                                # 调整结果格式以匹配后续处理
                                if theme_results.get("documents") and theme_results["documents"][0]:
                                    theme_results["ids"] = [[f"{theme}_{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
                                    print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
                                    all_results.append((theme, theme_results))
                                else:
                                    print(f"     ❌ 未找到结果")
                                    # 即使没有结果，也添加到all_results中，以确保后续处理能正确识别资源类型
                                    theme_results["ids"] = [[f"{theme}_{resource_type}_0"]]
                                    all_results.append((theme, theme_results))
                else:
                    # 单资源类型查询，使用统一的where_filter
                    for theme in themes_to_search:
                        # 使用ChromaDB的query方法进行相似度搜索
                        print(f"\n  🔍 为主题 '{theme}' 执行检索...")
                        
                        # 构建查询参数
                        n_results_per_theme = n_results or self.DEFAULT_N_RESULTS
                        
                        # V51.0改进：动态调整检索数量
                        n_results_per_theme = self._adjust_retrieval_count(query, detected_intents, n_results_per_theme)
                        
                        # V52.0改进：多主题查询增加检索数量
                        if len(themes_to_search) > 1:
                            n_results_per_theme = max(n_results_per_theme, 800)
                            print(f"   🔍 V52.0多主题查询: 增加检索数量到 {n_results_per_theme}")
                        
                        # 针对函数性质主题（单调性、奇偶性、周期性）增加检索数量
                        if any(prop in theme for prop in ["函数的单调性", "函数的奇偶性", "函数的周期性"]):
                            n_results_per_theme = max(n_results_per_theme, 900)
                            print(f"   🔍 函数性质查询: 增加检索数量到 {n_results_per_theme}")
                        
                        # V46.0改进：对于单调性证明题，增加检索数量以确保能找到相关习题
                        if question_type == '证明题' and ('单调性' in theme or '单调' in theme):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V46.0单调性证明题: 增加检索数量到 {n_results_per_theme}")
                        # V46.1改进：对于单调性证明题，即使主题中没有单调性，也增加检索数量
                        elif question_type == '证明题' and ('单调性' in query or '单调' in query):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V46.1单调性证明题: 增加检索数量到 {n_results_per_theme}")
                        # V48.0改进：对于函数选择题，增加检索数量以确保能找到相关习题
                        elif question_type == '选择题' and ('函数' in theme or '函数' in query):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V48.0函数选择题: 增加检索数量到 {n_results_per_theme}")
                        # V48.0改进：对于二次函数选择题，增加检索数量以确保能找到相关习题
                        elif question_type == '选择题' and ('二次函数' in theme or '二次函数' in query):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V48.0二次函数选择题: 增加检索数量到 {n_results_per_theme}")
                        # V48.0改进：对于三角函数习题，增加检索数量以确保能找到相关习题
                        elif ('三角函数' in theme or '三角函数' in query) and ('习题' in query or '题目' in query or '练习题' in query):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V48.0三角函数习题: 增加检索数量到 {n_results_per_theme}")
                        # V48.0改进：对于高二的三角函数习题，增加检索数量以确保能找到相关习题
                        elif ('高二' in query or '高中' in query) and ('三角函数' in theme or '三角函数' in query):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V48.0高二三角函数习题: 增加检索数量到 {n_results_per_theme}")
                        # V52.0改进：对于应用题查询，增加检索数量
                        elif any(kw in query for kw in ['应用题', '实际应用', '生活应用']):
                            n_results_per_theme = max(n_results_per_theme, 600)
                            print(f"   🔍 V52.0应用题查询: 增加检索数量到 {n_results_per_theme}")
                        # V54.0改进：对于教案查询，增加检索数量以确保能找到相关教案
                        elif '教案' in query or (resource_types and '教案' in resource_types):
                            n_results_per_theme = max(n_results_per_theme, 500)
                            print(f"   🔍 V54.0教案查询: 增加检索数量到 {n_results_per_theme}")
                        # 对于课件查询，增加检索数量以确保能找到相关课件
                        elif '课件' in query or (resource_types and '课件' in resource_types):
                            n_results_per_theme = max(n_results_per_theme, 900)
                            print(f"   🔍 课件查询: 增加检索数量到 {n_results_per_theme}")
                        
                        # 使用ChromaDB的query方法
                        theme_results = collection.query(
                            query_texts=[theme],
                            n_results=n_results_per_theme,
                            where=where_filter,
                            include=["documents", "metadatas", "distances"]
                        )
                        
                        # 调整结果格式以匹配后续处理
                        theme_results["ids"] = [[f"{theme}_{i}" for i in range(len(theme_results["documents"][0]))]]
                        
                        if theme_results.get("documents") and theme_results["documents"][0]:
                            print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
                            # 打印前3条结果的题目类型和来源
                            for i in range(min(3, len(theme_results['documents'][0]))):
                                meta = theme_results['metadatas'][0][i]
                                ex_type = meta.get('题目类型', '未知')
                                source = meta.get('source_file', '未知')
                                print(f"       - 结果{i+1}: 题目类型={ex_type}, 来源={source}")
                        else:
                            print(f"     ❌ 未找到结果")
                        
                        if theme_results.get("documents") and theme_results["documents"][0]:
                            all_results.append((theme, theme_results))
                
                # 合并多个主题的检索结果
                print("\n🔄 调用_merge_multi_theme_results函数...")
                merged_results = self._merge_multi_theme_results(all_results)
                print(f"✅ 合并完成，共 {len(merged_results['documents'][0])} 条结果")
                
                # 去重（基于题目内容）
                if merged_results and merged_results.get('metadatas') and merged_results['metadatas'][0]:
                    unique_results = self._deduplicate_results(merged_results)
                    print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
                    results = unique_results
                else:
                    results = merged_results
                
                # V10.0改进：对于综合题查询，增强多主题匹配
                if '综合题' in query or '综合' in query or '综合练习' in query or '数学综合' in query:
                    print("\n✨ V10.0：检测到综合题查询，增强多主题匹配...")
                    # 对合并结果进行综合题过滤
                    综合题_results = {
                        "documents": [[]],
                        "metadatas": [[]],
                        "distances": [[]],
                        "ids": [[]]
                    }
                    
                    for i, meta in enumerate(merged_results['metadatas'][0]):
                        # 检查是否是综合题
                        doc = merged_results['documents'][0][i]
                        question = meta.get('题干', '') or doc
                        knowledge_tags = meta.get('知识点', '') or meta.get('知识点标签', '')
                        
                        # 综合题特征：
                        # 1. 题干较长
                        # 2. 涉及多个知识点
                        # 3. 包含综合相关关键词
                        is_comprehensive = False
                        
                        # 特征1：题干长度
                        if len(question) > 150:
                            is_comprehensive = True
                        
                        # 特征2：多个知识点
                        if not is_comprehensive and knowledge_tags:
                            knowledge_points = [kp.strip() for kp in knowledge_tags.split(';') if kp.strip()]
                            if len(knowledge_points) > 2:
                                is_comprehensive = True
                        
                        # 特征3：综合相关关键词
                        if not is_comprehensive:
                            comprehensive_keywords = ['综合', '应用', '实际问题', '多知识点', '跨章节', '综合题', '综合练习']
                            all_info = f"{question} {knowledge_tags} {meta.get('标题', '')}"
                            for keyword in comprehensive_keywords:
                                if keyword in all_info:
                                    is_comprehensive = True
                                    break
                        
                        if is_comprehensive:
                            综合题_results['documents'][0].append(merged_results['documents'][0][i])
                            综合题_results['metadatas'][0].append(merged_results['metadatas'][0][i])
                            综合题_results['distances'][0].append(merged_results['distances'][0][i])
                            综合题_results['ids'][0].append(merged_results['ids'][0][i])
                    
                    if 综合题_results['documents'][0]:
                        print(f"✅ 筛选出 {len(综合题_results['documents'][0])} 条综合题")
                        results = 综合题_results
                    else:
                        # 如果没有找到综合题，返回原始结果
                        print(f"⚠️ 未找到综合题，返回原始结果")
            else:
                # 单主题查询，优先使用提取的核心主题
                # V83.0改进：当用户明确指定了资源类型时，使用原始查询作为查询文本
                if resource_types and not any(rt in ["资料", "资源"] for rt in resource_types):
                    # 使用原始查询作为查询文本
                    query_to_use = query
                    print(f"\n🔍 V83.0执行资源类型查询，使用原始查询作为查询文本: '{query_to_use}'")
                else:
                    # V66.0改进：当core_theme为空时，使用默认主题"函数"作为查询文本
                    if not core_theme:
                        core_theme = "函数"
                        print(f"   📝 V66.0使用默认主题: '{core_theme}'")
                    query_to_use = core_theme
                    print(f"\n🔍 执行单主题检索，查询: '{query_to_use}'")
                
                # 构建资源类型过滤条件
                resource_type_filters = []
                where_filter = None  # V55.1修复：初始化where_filter变量
                print(f"   🔍 V56.4调试 - 构建资源类型过滤条件，resource_types: {resource_types}")
                if resource_types and not any(rt in ["资料", "资源"] for rt in resource_types):
                    print(f"   🔍 V56.4调试 - 进入资源类型过滤条件块")
                    # 检查是否是教案、教学大纲、GGB等需要特殊处理的资源类型
                    special_resource_types = ["教案", "教学设计", "教学方案", "教学大纲", "大纲", "课程标准", "课件", "PPT", "幻灯片", "课例", "教学视频", "课堂实录", "GGB", "GeoGebra", "动态图", "可视化"]
                    is_special = any(rt in special_resource_types for rt in resource_types)
                    
                    db_types = []
                    for user_type in resource_types:
                        mapped_db_type = get_db_type(user_type)
                        print(f"   🔍 V56.4调试 - 映射资源类型: {user_type} -> {mapped_db_type}")
                        if mapped_db_type:
                            db_types.append(mapped_db_type)
                    print(f"   🔍 V56.4调试 - db_types: {db_types}, len: {len(db_types)}")
                    if db_types:
                        # 对于多个资源类型，为每种类型创建单独的过滤条件
                        if len(db_types) > 1:
                            print(f"   📋 V54.0组合资源查询: 为每种资源类型单独检索")
                            print(f"   🔍 V56.4调试 - 为每种资源类型创建过滤条件: {db_types}")
                            for db_type in db_types:
                                resource_type_filters.append({"resource_type": db_type})
                        else:
                            # 对于单个资源类型，使用等于操作符
                            where_filter = {"resource_type": db_types[0]}
                            if is_special:
                                print(f"   📋 V54.0特殊资源类型过滤: {db_types[0]}")
                            else:
                                print(f"   📋 资源类型过滤: {db_types[0]}")
                # 对于综合资源查询，不设置过滤条件，允许返回所有资源类型
                elif not resource_types or any(rt in ["资料", "资源"] for rt in resource_types):
                    print(f"   📋 综合资源查询: 不设置资源类型过滤")
                # V46.1改进：对于单调性证明题查询，强制添加exercise过滤
                elif question_type == '证明题' and ('单调性' in query or '单调' in query):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V46.1单调性证明题：强制添加exercise过滤")
                # V48.0改进：对于函数选择题查询，强制添加exercise过滤
                elif question_type == '选择题' and ('函数' in query or '二次函数' in query or '三角函数' in query):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V48.0函数选择题：强制添加exercise过滤")
                # V52.0改进：对于习题、题目、练习题、例子、应用题查询，强制添加exercise过滤
                # 注意：只在用户明确要求习题资源时才添加过滤，避免影响教案、教学大纲等其他资源类型的查询
                # 只有当resource_type_filters为空时才执行这个过滤
                elif not resource_type_filters and any(kw in query for kw in ['习题', '题目', '练习题', '例子', '实例', '案例', '应用题', '实际应用', '生活应用']) and not any(kw in query for kw in ['教案', '教学设计', '教学方案', '教学大纲', '大纲', '课程标准', '课件', 'PPT', '幻灯片', '课例', '教学视频', '课堂实录', 'GGB', 'GeoGebra', '动态图', '可视化']):
                    where_filter = {"resource_type": "exercise"}
                    print(f"   📋 V52.0习题查询：强制添加exercise过滤")
                
                # V51.0改进：使用动态意图识别系统
                detected_intents = self._detect_query_intents(query)
                
                # V51.0改进：动态增强查询
                # 注意：对于核心主题查询，我们直接使用核心主题作为查询文本，
                # 而不是使用增强后的查询，以确保能够找到包含核心主题的资源
                if core_theme:
                    enhanced_query = core_theme
                    print(f"   🔍 V51.0使用核心主题作为查询文本: '{enhanced_query}'")
                else:
                    enhanced_query = self._enhance_query_dynamically(query_to_use, detected_intents)
                    print(f"   🔍 V51.0动态查询增强: '{query_to_use}' -> '{enhanced_query}'")
                
                # 使用ChromaDB的query方法进行相似度搜索
                n_results_per_query = n_results or self.DEFAULT_N_RESULTS
                
                # V51.0改进：动态调整检索数量
                n_results_adjusted = self._adjust_retrieval_count(query_to_use, detected_intents, n_results_per_query, resource_types)
                
                # V51.0改进：对于核心主题查询，增加检索数量以确保能找到包含核心主题的资源
                if core_theme:
                    n_results_adjusted = max(n_results_adjusted, 50)
                    print(f"   🔍 V51.0核心主题查询: 增加检索数量到 {n_results_adjusted}")
                
                # 保留原有的特定查询处理逻辑（作为后备）
                # V46.0改进：对于单调性证明题，增加检索数量以确保能找到相关习题
                if (question_type == '证明题' and '单调性' in query) or ('证明' in query and '单调性' in query):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V46.0单调性证明题后备: 增加检索数量到 {n_results_adjusted}")
                # V50.0改进：对于奇偶性证明题，增加检索数量以确保能找到相关习题
                elif (question_type == '证明题' and '奇偶性' in query) or ('证明' in query and '奇偶性' in query):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V50.0奇偶性证明题后备: 增加检索数量到 {n_results_adjusted}")
                # V48.0改进：对于函数选择题，增加检索数量以确保能找到相关习题
                elif question_type == '选择题' and ('函数' in query or '函数' in query_to_use):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V48.0函数选择题后备: 增加检索数量到 {n_results_adjusted}")
                # V48.0改进：对于二次函数选择题，增加检索数量以确保能找到相关习题
                elif question_type == '选择题' and ('二次函数' in query or '二次函数' in query_to_use):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V48.0二次函数选择题后备: 增加检索数量到 {n_results_adjusted}")
                # V48.0改进：对于三角函数习题，增加检索数量以确保能找到相关习题
                elif ('三角函数' in query or '三角函数' in query_to_use) and ('习题' in query or '题目' in query or '练习题' in query):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V48.0三角函数习题后备: 增加检索数量到 {n_results_adjusted}")
                # V48.0改进：对于高二的三角函数习题，增加检索数量以确保能找到相关习题
                elif ('高二' in query or '高中' in query) and ('三角函数' in query or '三角函数' in query_to_use):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V48.0高二三角函数习题后备: 增加检索数量到 {n_results_adjusted}")
                # V52.0改进：对于应用题，增加检索数量以确保能找到相关习题
                elif any(kw in query for kw in ['应用题', '实际应用', '生活应用', '例子', '实例', '案例']):
                    n_results_adjusted = max(n_results_adjusted, 600)
                    print(f"   🔍 V52.0应用题/例子: 增加检索数量到 {n_results_adjusted}")
                # V54.0改进：对于教案查询，增加检索数量以确保能找到相关教案
                elif '教案' in query or (resource_types and '教案' in resource_types):
                    n_results_adjusted = max(n_results_adjusted, 500)
                    print(f"   🔍 V54.0教案查询: 增加检索数量到 {n_results_adjusted}")
                else:
                    print(f"   🔍 V46.0调试: 条件不满足，使用默认检索数量 {n_results_adjusted}")
                
                # V54.1改进：对于组合资源查询，为每种资源类型单独执行检索
                if resource_type_filters:
                    print(f"\n  🔍 V54.1组合资源查询: 为 {len(resource_type_filters)} 种资源类型单独检索")
                    
                    all_results = []
                    for resource_filter in resource_type_filters:
                        resource_type = resource_filter['resource_type']
                        print(f"\n  🔍 为资源类型 '{resource_type}' 执行检索...")
                        
                        # V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索
                        # 资源类型过滤对于课件资源特别重要，因为课件资源的文档内容质量较差
                        print(f"   📋 V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索")
                        theme_results = collection.query(
                            query_texts=[enhanced_query],
                            n_results=n_results_adjusted,
                            where=resource_filter,  # 重新启用资源类型过滤
                            include=["documents", "metadatas", "distances"]
                        )
                        
                        # 调整结果格式以匹配后续处理
                        theme_results["ids"] = [[f"{resource_type}_{i}" for i in range(len(theme_results["documents"][0]))]]
                        
                        if theme_results.get("documents") and theme_results["documents"][0]:
                            print(f"     ✅ 找到 {len(theme_results['documents'][0])} 条结果")
                            all_results.append((resource_type, theme_results))
                        else:
                            print(f"     ❌ 未找到结果")
                    
                    # 合并多个资源类型的检索结果
                    if all_results:
                        print(f"\n🔄 合并 {len(all_results)} 种资源类型的检索结果...")
                        merged_results = {
                            "documents": [[]],
                            "metadatas": [[]],
                            "distances": [[]],
                            "ids": [[]]
                        }
                        
                        for resource_type, theme_results in all_results:
                            merged_results["documents"][0].extend(theme_results["documents"][0])
                            merged_results["metadatas"][0].extend(theme_results["metadatas"][0])
                            merged_results["distances"][0].extend(theme_results["distances"][0])
                            merged_results["ids"][0].extend(theme_results["ids"][0])
                        
                        results = merged_results
                        print(f"✅ 合并完成，共 {len(results['documents'][0])} 条结果")
                    else:
                        print(f"❌ 所有资源类型均未找到结果")
                        results = None
                else:
                    # V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索
                    # 资源类型过滤对于课件资源特别重要，因为课件资源的文档内容质量较差
                    print(f"   📋 V90.0修复：重新启用资源类型过滤，确保课件资源能被正确检索")
                    results = collection.query(
                        query_texts=[enhanced_query],
                        n_results=n_results_adjusted,
                        where=where_filter,  # 重新启用资源类型过滤
                        include=["documents", "metadatas", "distances"]
                    )
                    
                    # 调整结果格式以匹配后续处理
                    results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]
                
                if results and results.get('documents') and results['documents'][0]:
                    # 调整结果格式以匹配后续处理
                    if not results.get("ids") or not results["ids"][0]:
                        results["ids"] = [[f"query_{i}" for i in range(len(results["documents"][0]))]]
                    
                    # 去重（基于题目内容）
                    if results and results.get('metadatas') and results['metadatas'][0]:
                        unique_results = self._deduplicate_results(results)
                        print(f"   ✅ 去重后剩余{len(unique_results['ids'][0])}个资源")
                        results = unique_results
                    
                    # V64.0改进：对于单主题查询，为课件和教案资源设置更宽松的相似度阈值
                    # 模拟多主题查询的处理逻辑，为课件和教案资源设置更宽松的阈值
                    filtered_results = {
                        "documents": [[]],
                        "metadatas": [[]],
                        "distances": [[]],
                        "ids": [[]]
                    }
                    
                    # V74.0改进：当用户明确指定了资源类型时，使用更宽松的相似度阈值
                    if resource_types and not any(rt in ["资料", "资源"] for rt in resource_types):
                        # 动态调整阈值
                        def get_dynamic_threshold(query, resource_types, resource_type=None):
                            # 基础阈值
                            base_threshold = 1.5
                            
                            # 1. 根据资源类型调整
                            resource_type_adjustment = 0
                            if any(rt in ["教案", "教学设计", "教学方案", "课件", "PPT", "幻灯片"] for rt in resource_types):
                                resource_type_adjustment = 8.5  # 教案和课件资源使用更宽松的阈值
                            elif any(rt in ["GGB", "GeoGebra", "动态图", "可视化"] for rt in resource_types):
                                resource_type_adjustment = 6.0  # GGB资源使用较宽松的阈值
                            elif any(rt in ["习题", "题目", "练习题", "测试题"] for rt in resource_types):
                                resource_type_adjustment = 1.5  # 习题资源使用中等阈值
                            elif any(rt in ["课例", "教学视频", "课堂实录"] for rt in resource_types):
                                resource_type_adjustment = 4.0  # 课例资源使用较宽松的阈值
                            elif any(rt in ["教学大纲", "大纲", "课程标准"] for rt in resource_types):
                                resource_type_adjustment = 5.0  # 教学大纲资源使用较宽松的阈值
                            
                            # 2. 根据查询意图调整
                            intent_adjustment = 0
                            query_conditions = self._extract_query_conditions(query)
                            intent = query_conditions.get('intent', '')
                            if intent == '练习':
                                intent_adjustment = 0.5  # 练习查询需要更精确的资源
                            elif intent == '学习':
                                intent_adjustment = 1.0  # 学习查询可以更宽松
                            elif intent == '教学':
                                intent_adjustment = 2.0  # 教学查询需要更全面的资源
                            elif intent == '复习':
                                intent_adjustment = 1.5  # 复习查询需要较全面的资源
                            elif intent == '比较':
                                intent_adjustment = 2.5  # 比较查询需要多个相关主题的资源
                            
                            # 3. 根据查询复杂度调整
                            complexity_adjustment = 0
                            if len(query) > 30:
                                complexity_adjustment = 1.0  # 复杂查询可以更宽松
                            elif len(query) < 10:
                                complexity_adjustment = -0.5  # 简单查询需要更精确
                            
                            # 4. 根据资源类型微调
                            if resource_type:
                                if resource_type == 'courseware' or resource_type == 'lesson_plan':
                                    resource_type_adjustment += 1.0
                                elif resource_type == 'exercise':
                                    resource_type_adjustment -= 0.5
                            
                            # 计算最终阈值
                            final_threshold = base_threshold + resource_type_adjustment + intent_adjustment + complexity_adjustment
                            # 确保阈值在合理范围内
                            final_threshold = max(1.0, min(15.0, final_threshold))
                            return final_threshold
                        
                        # 为每个资源动态计算阈值
                        for i, (doc, meta, dist, id_) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0])):
                            resource_type = meta.get('resource_type', '')
                            strict_threshold = get_dynamic_threshold(query, resource_types, resource_type)
                            
                            # 检查资源是否包含核心主题
                            contains_core_theme = core_theme and (core_theme in doc or core_theme in meta.get('title', '') or core_theme in str(meta))
                            
                            if dist < strict_threshold or contains_core_theme:
                                filtered_results["documents"][0].append(doc)
                                filtered_results["metadatas"][0].append(meta)
                                filtered_results["distances"][0].append(dist)
                                filtered_results["ids"][0].append(id_)
                                if contains_core_theme:
                                    print(f"   ✅ 保留（包含核心主题）：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
                                else:
                                    print(f"   ✅ 保留：'{meta.get('title', '未知')}' (距离: {dist:.3f} < {strict_threshold})")
                            else:
                                print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 相似度过低 (距离: {dist:.3f} >= {strict_threshold})")
                    else:
                        # 对于普通查询，使用动态阈值逻辑
                        def get_dynamic_threshold(query, resource_type):
                            # 基础阈值
                            base_threshold = 1.5
                            
                            # 1. 根据资源类型调整
                            resource_type_adjustment = 0
                            if resource_type == 'courseware' or resource_type == 'lesson_plan':
                                resource_type_adjustment = 1.5  # 课件和教案资源使用更宽松的阈值
                            elif resource_type == 'ggb':
                                resource_type_adjustment = 2.0  # GGB资源使用较宽松的阈值
                            elif resource_type == 'syllabus':
                                resource_type_adjustment = 2.5  # 教学大纲资源使用较宽松的阈值
                            elif resource_type == 'lesson_case':
                                resource_type_adjustment = 2.0  # 课例资源使用较宽松的阈值
                            elif resource_type == 'exercise':
                                resource_type_adjustment = 0  # 习题资源使用标准阈值
                            
                            # 2. 根据查询意图调整
                            intent_adjustment = 0
                            query_conditions = self._extract_query_conditions(query)
                            intent = query_conditions.get('intent', '')
                            if intent == '练习':
                                intent_adjustment = -0.5  # 练习查询需要更精确的资源
                            elif intent == '学习':
                                intent_adjustment = 0.5  # 学习查询可以更宽松
                            elif intent == '教学':
                                intent_adjustment = 1.0  # 教学查询需要更全面的资源
                            elif intent == '复习':
                                intent_adjustment = 0.8  # 复习查询需要较全面的资源
                            elif intent == '比较':
                                intent_adjustment = 1.2  # 比较查询需要多个相关主题的资源
                            
                            # 3. 根据查询复杂度调整
                            complexity_adjustment = 0
                            if len(query) > 30:
                                complexity_adjustment = 0.5  # 复杂查询可以更宽松
                            elif len(query) < 10:
                                complexity_adjustment = -0.3  # 简单查询需要更精确
                            
                            # 计算最终阈值
                            final_threshold = base_threshold + resource_type_adjustment + intent_adjustment + complexity_adjustment
                            # 确保阈值在合理范围内
                            final_threshold = max(0.8, min(10.0, final_threshold))
                            return final_threshold
                        
                        for i, (doc, meta, dist, id_) in enumerate(zip(results["documents"][0], results["metadatas"][0], results["distances"][0], results["ids"][0])):
                            resource_type = meta.get('resource_type', '')
                            strict_threshold = get_dynamic_threshold(query, resource_type)
                            print(f"   🔍 动态阈值调整：为{resource_type}资源使用阈值 {strict_threshold:.2f}")
                            
                            # 检查资源是否包含核心主题
                            contains_core_theme = core_theme and (core_theme in doc or core_theme in meta.get('title', ''))
                            
                            if dist < strict_threshold or contains_core_theme:
                                filtered_results["documents"][0].append(doc)
                                filtered_results["metadatas"][0].append(meta)
                                filtered_results["distances"][0].append(dist)
                                filtered_results["ids"][0].append(id_)
                                if contains_core_theme:
                                    print(f"   ✅ 保留（包含核心主题）：'{meta.get('title', '未知')}' (距离: {dist:.3f})")
                                else:
                                    print(f"   ✅ 保留：'{meta.get('title', '未知')}' (距离: {dist:.3f} < {strict_threshold:.2f})")
                            else:
                                print(f"   ⚠️ 过滤：'{meta.get('title', '未知')}' 相似度过低 (距离: {dist:.3f} >= {strict_threshold:.2f})")
                    
                    if filtered_results["documents"][0]:
                        results = filtered_results
                        print(f"   ✅ V64.0单主题查询过滤完成，保留 {len(results['documents'][0])} 条结果")
                    else:
                        print(f"   ❌ V64.0单主题查询过滤后无结果")
                        results = None
                
                # V92.0改进：优化难度筛选功能，使用难度1-5字段
                if difficulty_info:
                    print(f"🔍 V92.0应用难度筛选: {difficulty_info}")
                    difficulty_level = difficulty_info.get("difficulty", "")
                    if difficulty_level:
                        filtered_results = {
                            "documents": [[]],
                            "metadatas": [[]],
                            "distances": [[]],
                            "ids": [[]]
                        }
                        
                        # V92.0改进：使用难度1-5字段进行筛选
                        for i, meta in enumerate(results["metadatas"][0]):
                            # 获取资源的难度（1-5）
                            resource_difficulty = meta.get('难度（1-5）', 3)
                            
                            # 如果没有难度字段，尝试其他可能的字段名
                            if resource_difficulty is None or resource_difficulty == '':
                                resource_difficulty = meta.get('难度', 3)
                            
                            # 转换为整数
                            try:
                                resource_difficulty = int(resource_difficulty)
                            except (ValueError, TypeError):
                                resource_difficulty = 3  # 默认中等难度
                            
                            # 筛选逻辑
                            if difficulty_level == '基础':
                                # 基础题：难度1-2
                                if resource_difficulty <= 2:
                                    filtered_results["documents"][0].append(results["documents"][0][i])
                                    filtered_results["metadatas"][0].append(meta)
                                    filtered_results["distances"][0].append(results["distances"][0][i])
                                    filtered_results["ids"][0].append(results["ids"][0][i])
                            elif difficulty_level == '中等':
                                # 中等题：难度2-3
                                if 2 <= resource_difficulty <= 3:
                                    filtered_results["documents"][0].append(results["documents"][0][i])
                                    filtered_results["metadatas"][0].append(meta)
                                    filtered_results["distances"][0].append(results["distances"][0][i])
                                    filtered_results["ids"][0].append(results["ids"][0][i])
                            elif difficulty_level == '困难' or difficulty_level == '难':
                                # 困难题：难度3-5
                                if resource_difficulty >= 3:
                                    filtered_results["documents"][0].append(results["documents"][0][i])
                                    filtered_results["metadatas"][0].append(meta)
                                    filtered_results["distances"][0].append(results["distances"][0][i])
                                    filtered_results["ids"][0].append(results["ids"][0][i])
                            elif difficulty_level == '综合':
                                # 综合题：包含多个知识点或应用题
                                knowledge_tags = meta.get('知识点标签', '')
                                has_multiple_topics = len(knowledge_tags.split(';')) >= 2 if knowledge_tags else False
                                has_application = any(kw in (meta.get('title', '') + meta.get('题干', '')) for kw in ['应用', '实际', '利润', '面积', '模型', '建模'])
                                
                                if has_multiple_topics or has_application:
                                    filtered_results["documents"][0].append(results["documents"][0][i])
                                    filtered_results["metadatas"][0].append(meta)
                                    filtered_results["distances"][0].append(results["distances"][0][i])
                                    filtered_results["ids"][0].append(results["ids"][0][i])
                        
                        # 使用筛选后的结果
                        if filtered_results["documents"][0]:
                            results = filtered_results
                            print(f"     ✅ V92.0难度筛选完成，保留 {len(results['documents'][0])} 条结果")
                        else:
                            print(f"     ⚠️ V92.0难度筛选后无结果，返回原始结果")
                    else:
                        # V95.0改进：如果用户指定了数量限制但资源不足，放宽难度限制
                        if self._current_quantity_limit and len(results['documents'][0]) < self._current_quantity_limit:
                            print(f"     ⚠️ V95.0资源不足，放宽难度限制（当前: {len(results['documents'][0])} 条, 要求: {self._current_quantity_limit} 条）")
                            # 不进行难度筛选，保留所有结果
                            print(f"     ✅ V95.0保留所有结果，数量: {len(results['documents'][0])}")
                
                # V92.0改进：优化题目类型筛选功能，通过题目内容判断题型
                if question_type:
                    print(f"🔍 V92.0应用题目类型筛选: {question_type}")
                    print(f"   🔍 V92.0调试 - 原始结果数量: {len(results['documents'][0])}")
                    filtered_results = {
                        "documents": [[]],
                        "metadatas": [[]],
                        "distances": [[]],
                        "ids": [[]]
                    }
                    
                    exercise_count = 0
                    other_count = 0
                    
                    for i, meta in enumerate(results["metadatas"][0]):
                        # 获取资源的资源类型
                        db_resource_type = meta.get('resource_type', '')
                        
                        # V92.0改进：只筛选习题资源，保留其他资源类型
                        if db_resource_type == 'exercise':
                            # V92.0改进：通过题目内容判断题型
                            question_type_field = meta.get('题目类型', '')
                            question_content = meta.get('题干', '')
                            
                            # 筛选逻辑
                            is_match = False
                            if question_type == '选择题':
                                # 选择题特征：包含选项、括号、A. B. C. D.等
                                if '选择题' in question_type_field or '单选' in question_type_field or '多选' in question_type_field:
                                    is_match = True
                                elif any(kw in question_content for kw in ['A.', 'B.', 'C.', 'D.', 'A、', 'B、', 'C、', 'D、', '（A）', '（B）', '（C）', '（D）']):
                                    is_match = True
                            elif question_type == '填空题':
                                # 填空题特征：包含下划线、横线、空格等
                                if '填空题' in question_type_field or '填空' in question_type_field:
                                    is_match = True
                                elif any(kw in question_content for kw in ['______', '_____', '____', '___', '__', '（    ）', '（   ）', '（  ）', '（ ）']):
                                    is_match = True
                            elif question_type == '解答题':
                                # 解答题特征：包含"解"、"证明"、"求"、"计算"等
                                if '解答题' in question_type_field or '计算题' in question_type_field or '应用题' in question_type_field:
                                    is_match = True
                                elif any(kw in question_content for kw in ['解：', '证明：', '求：', '计算：', '求解', '证明', '解答', '计算']):
                                    is_match = True
                            elif question_type == '证明题':
                                # 证明题特征：包含"证明"、"求证"等
                                if '证明题' in question_type_field or '证明' in question_type_field:
                                    is_match = True
                                elif any(kw in question_content for kw in ['证明：', '求证：', '证明', '求证', '∵', '∴']):
                                    is_match = True
                            
                            if is_match:
                                filtered_results["documents"][0].append(results["documents"][0][i])
                                filtered_results["metadatas"][0].append(meta)
                                filtered_results["distances"][0].append(results["distances"][0][i])
                                filtered_results["ids"][0].append(results["ids"][0][i])
                                exercise_count += 1
                        else:
                            # V92.0改进：非习题资源（教案、课件等）直接保留
                            filtered_results["documents"][0].append(results["documents"][0][i])
                            filtered_results["metadatas"][0].append(meta)
                            filtered_results["distances"][0].append(results["distances"][0][i])
                            filtered_results["ids"][0].append(results["ids"][0][i])
                            other_count += 1
                    
                    print(f"   🔍 V92.0调试 - 保留习题: {exercise_count}条, 其他资源: {other_count}条")
                    
                    # 使用筛选后的结果
                    if filtered_results["documents"][0]:
                        results = filtered_results
                        print(f"     ✅ V92.0题目类型筛选完成，保留 {len(results['documents'][0])} 条结果")
                    else:
                        # V95.0改进：如果用户指定了数量限制但资源不足，放宽题目类型限制
                        if self._current_quantity_limit:
                            print(f"     ⚠️ V95.0题目类型筛选后无结果，返回原始结果（数量限制: {self._current_quantity_limit}）")
                        else:
                            print(f"     ⚠️ V92.0题目类型筛选后无结果，返回原始结果")
                # V61.0改进：使用动态配置获取函数类型，避免硬编码
                core_theme = self._extract_core_theme(query)
                specific_function_types = self.config_loader.get_all_function_types()
                # 改进：检测纯函数查询，包括"函数题"、"函数"等板块级词汇
                is_pure_function_query = (core_theme == "函数" or "函数题" in query) and not any(func_type in query for func_type in specific_function_types)
                
                if is_pure_function_query and quantity_limit:
                    print(f"🔍 V48.2纯函数查询预过滤: 优先保留函数概念、性质等资源")
                    # 分离函数概念性质资源和其他资源
                    concept_property_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
                    other_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
                    
                    # 函数概念和性质相关的关键词
                    function_concept_keywords = [
                        "函数的概念", "函数的性质", "函数的单调性", "函数的奇偶性", "函数的周期性",
                        "函数的定义域", "函数的值域", "函数的图像", "函数的零点", "函数的应用"
                    ]
                    
                    for i, meta in enumerate(results["metadatas"][0]):
                        source_file = meta.get('source_file', '')
                        title = meta.get('title', '')
                        content = results["documents"][0][i]
                        
                        # 检查是否是函数概念或性质相关资源
                        is_concept_property = False
                        
                        # 检查来源文件
                        if '必修一第三章' in source_file or '第三章-函数的概念' in source_file:
                            is_concept_property = True
                        
                        # 检查标题和内容
                        if not is_concept_property:
                            all_info = f"{title} {content}"
                            for keyword in function_concept_keywords:
                                if keyword in all_info:
                                    is_concept_property = True
                                    break
                        
                        if is_concept_property:
                            concept_property_results["documents"][0].append(results["documents"][0][i])
                            concept_property_results["metadatas"][0].append(meta)
                            concept_property_results["distances"][0].append(results["distances"][0][i])
                            concept_property_results["ids"][0].append(results["ids"][0][i])
                        else:
                            other_results["documents"][0].append(results["documents"][0][i])
                            other_results["metadatas"][0].append(meta)
                            other_results["distances"][0].append(results["distances"][0][i])
                            other_results["ids"][0].append(results["ids"][0][i])
                    
                    print(f"     ✅ 函数概念性质资源: {len(concept_property_results['documents'][0])} 条")
                    print(f"     ✅ 其他资源: {len(other_results['documents'][0])} 条")
                    
                    # 优先保留函数概念性质资源，然后补充其他资源
                    combined_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
                    combined_results["documents"][0] = concept_property_results["documents"][0] + other_results["documents"][0]
                    combined_results["metadatas"][0] = concept_property_results["metadatas"][0] + other_results["metadatas"][0]
                    combined_results["distances"][0] = concept_property_results["distances"][0] + other_results["distances"][0]
                    combined_results["ids"][0] = concept_property_results["ids"][0] + other_results["ids"][0]
                    
                    results = combined_results
                
                # V33.0改进：应用数量限制
                if quantity_limit and len(results["documents"][0]) > quantity_limit:
                    # 首先筛选出包含核心主题的资源
                    core_theme_resources = []
                    other_resources = []
                    
                    for i, meta in enumerate(results["metadatas"][0]):
                        # 检查资源是否包含核心主题
                        contains_core_theme = False
                        if core_theme:
                            # 检查文档内容、标题和元数据是否包含核心主题
                            content = results["documents"][0][i] or ""
                            title = meta.get('title', '') or ""
                            metadata_str = str(meta) or ""
                            contains_core_theme = core_theme in content or core_theme in title or core_theme in metadata_str
                        
                        if contains_core_theme:
                            core_theme_resources.append(i)
                        else:
                            other_resources.append(i)
                    
                    # 优先保留包含核心主题的资源，然后补充其他资源
                    prioritized_indices = core_theme_resources + other_resources
                    prioritized_indices = prioritized_indices[:quantity_limit]  # 限制数量
                    
                    # 重新构建结果
                    prioritized_results = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
                    for idx in prioritized_indices:
                        prioritized_results["documents"][0].append(results["documents"][0][idx])
                        prioritized_results["metadatas"][0].append(results["metadatas"][0][idx])
                        prioritized_results["distances"][0].append(results["distances"][0][idx])
                        prioritized_results["ids"][0].append(results["ids"][0][idx])
                    
                    results = prioritized_results
                    print(f"🔍 V33.0应用数量限制: {quantity_limit}")
                    print(f"     ✅ V33.0数量限制应用完成，返回 {len(results['documents'][0])} 条结果")
                    print(f"     ✅ 其中包含核心主题的资源: {min(len(core_theme_resources), quantity_limit)} 条")
                
                if results.get("documents") and results["documents"][0]:
                    print(f"     ✅ 找到 {len(results['documents'][0])} 条结果")
                    # 打印前3条结果的题目类型和来源
                    for i in range(min(3, len(results['documents'][0]))):
                        meta = results['metadatas'][0][i]
                        ex_type = meta.get('题目类型', '未知')
                        source = meta.get('source_file', '未知')
                        print(f"       - 结果{i+1}: 题目类型={ex_type}, 来源={source}")
                else:
                    print(f"     ❌ 未找到结果")
            
            # 打印查询结果的基本信息
            if results.get("documents") and results["documents"][0]:
                print(f"📊 查询返回 {len(results['documents'][0])} 条结果")
                
                # V43.0改进：先提取题目类型，再进行资源分类
                question_type = self._extract_question_type(query)
                if question_type:
                    print(f"🔍 V43.0提取到题目类型: {question_type}")
                
                # 处理检索结果（V32.0修复：传递query参数）
                classified_resources = self._classify_results(results, resource_types, core_theme, query, question_type, grade, difficulty, exam_form)
                
                # V11.1：单主题检索时，使用LLM验证主题相关性
                # V11.2改进：暂时禁用LLM验证，避免模型未初始化导致所有资源被过滤
                # if len(core_themes) == 1:
                #     print(f"\n🔍 V11.1：单主题检索，使用LLM验证主题相关性...")
                #     theme = core_themes[0]
                #     
                #     # 过滤不相关的资源
                #     filtered_resources = []
                #     for category in classified_resources:
                #         if isinstance(classified_resources[category], list):
                #             for resource in classified_resources[category]:
                #                 # 使用LLM判断资源是否与主题相关
                #                 doc = resource.get('content', '')
                #                 meta = resource.get('metadata', {})
                #                 
                #                 is_relevant = self._check_theme_relevance_with_llm(theme, doc, meta)
                #                 
                #                 if is_relevant:
                #                     filtered_resources.append(resource)
                #                 else:
                #                     print(f"      ⚠️ 过滤：'{meta.get('title', '未知')}' 与主题 '{theme}' 不相关")
                #     
                #     # 更新分类资源
                #     classified_resources = {}
                #     if filtered_resources:
                #         classified_resources["核心主题资源"] = filtered_resources
                #     
                #     print(f"✅ 单主题检索过滤完成，保留 {len(filtered_resources)} 条相关结果")
                
                # V8.2改进：主题精准匹配，过滤不相关资源
                if core_theme:
                    print(f"\n🔍 V8.2主题精准匹配（核心主题: {core_theme}）...")
                    # 收集所有资源
                    all_resources = []
                    for category in classified_resources:
                        # 只处理值是列表的键，跳过message等非资源列表键
                        if isinstance(classified_resources[category], list):
                            for resource in classified_resources[category]:
                                # 确保resource是字典
                                if isinstance(resource, dict):
                                    # 添加分类信息作为辅助
                                    resource["_category"] = category
                                    all_resources.append(resource)
                                else:
                                    print(f"   ⚠️ 跳过非字典资源: {type(resource)}")
                    
                    # V8.3：过滤过于宽泛的主题（如单独的"函数"）
                    core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                    # 定义过于宽泛的主题列表
                    broad_themes = {"数学", "代数", "几何", "统计", "概率"}
                    # 对于教案、教学大纲等资源，"函数"不是过于宽泛的主题
                    # 对于习题资源，"函数"也不是过于宽泛的主题，应该返回函数相关的概念、性质等资源
                    # 对于包含"题"、"习题"、"练习题"的查询，相关主题也不是过于宽泛的主题
                    if resource_types or "题" in query or "习题" in query or "练习题" in query:
                        if any(rt in ["教案", "教学设计", "教学方案", "教学大纲", "大纲", "课程标准", "习题", "题目", "练习题"] for rt in resource_types) or "题" in query or "习题" in query or "练习题" in query:
                            # 对于包含"题"的查询，不移除任何主题
                            print(f"   ✅ 对于包含'题'的查询，保留所有主题")
                        else:
                            if "函数" in broad_themes:
                                broad_themes.remove("函数")
                                print(f"   ✅ 对于{resource_types}资源，'函数'不是过于宽泛的主题")
                    filtered_themes = [t for t in core_themes if t not in broad_themes]
                    
                    if len(filtered_themes) < len(core_themes):
                        print(f"   ⚠️ 过滤过于宽泛的主题: {set(core_themes) - set(filtered_themes)}")
                        core_theme = ",".join(filtered_themes) if filtered_themes else core_themes[0]
                        print(f"   ✅ 过滤后的核心主题: {core_theme}")
                    
                    # V8.3：分离可见资源和隐藏资源
                    visible_resources = [r for r in all_resources if r.get('should_show', True)]
                    hidden_resources = [r for r in all_resources if not r.get('should_show', True)]
                    
                    print(f"   🔍 V31.0 DEBUG: visible_resources数量={len(visible_resources)}, hidden_resources数量={len(hidden_resources)}")
                    
                    # V8.3：资源分布平衡逻辑
                    balanced_resources = self._balance_resource_distribution(visible_resources, core_theme, query)
                    
                    # 重新分类（用于展示时的分组）
                    classified_resources = self._reclassify_by_relevance(balanced_resources, core_theme)
                    
                    # V8.3：添加隐藏资源信息到结果中
                    classified_resources["_hidden_resources"] = hidden_resources
                    classified_resources["_hidden_count"] = len(hidden_resources)
                    classified_resources["_total_count"] = len(all_resources)
                    
                    print(f"   ✅ V8.3排序完成：核心主题优先，共{len(balanced_resources)}个可见资源（隐藏{len(hidden_resources)}个，总计{len(all_resources)}个）")
                else:
                    # 如果没有核心主题，保持原有的分类排序
                    # V9.1：应用内容匹配评分
                    query_features = getattr(self, '_current_query_features', {})
                    if query_features.get('has_content_requirement'):
                        print(f"\n🔍 V9.1应用内容匹配评分（无核心主题）...")
                        for category in classified_resources:
                            for resource in classified_resources[category]:
                                if 'content_features' in resource:
                                    content_score = self.content_extractor.calculate_content_match_score(
                                        resource['content_features'],
                                        query_features
                                    )
                                    original_relevance = resource.get('relevance', 0)
                                    resource['relevance'] = original_relevance * 0.7 + content_score * 0.3
                                    resource['content_match_score'] = content_score
                    
                    for category in classified_resources:
                        if classified_resources[category]:
                            classified_resources[category].sort(
                                key=lambda x: -x.get('relevance', 0)
                            )
                    
                    # 添加空的隐藏资源信息
                    classified_resources["_hidden_resources"] = []
                    classified_resources["_hidden_count"] = 0
                    classified_resources["_total_count"] = sum(len(resources) for resources in classified_resources.values() if isinstance(resources, list))
                
                print(f"✅ 检索完成: {self._get_summary(classified_resources)}")
                
                return classified_resources
            else:
                # 查询执行成功但没有任何匹配结果，返回空结构而不是 None
                print("ℹ️ 查询完成，但未命中任何资源")
                return self._get_empty_result()
            
        except Exception as e:
            print(f"❌ 资源检索失败: {str(e)}")
            return self._get_empty_result()
    
    def _check_vector_db_exists(self) -> bool:
        """
        检查向量数据库是否存在
        
        Returns:
            是否存在
        """
        return self.vector_db_builder.check_database_exists()
    
    def _generate_query_embedding(self, query: str, embedding_model) -> List[float]:
        """
        生成查询的向量表示
        
        Args:
            query: 查询文本
            embedding_model: Embedding模型
        
        Returns:
            查询向量
        """
        query_embedding = embedding_model.encode(
            [query], 
            normalize_embeddings=True
        ).tolist()
        
        print(f"📊 查询向量维度: {len(query_embedding[0])}")
        
        return query_embedding
    
    def _merge_multi_theme_results(self, all_results: List[Tuple[str, Dict[str, Any]]]) -> Dict[str, Any]:
        """
        合并多个主题的检索结果 - 改进版
        记录每个资源与各个主题的匹配关系
        
        关键修复：添加排除词检查，过滤不相关资源
        V47.0改进：增强对比查询处理
        V61.0改进：增强函数性质主题的处理
        
        Args:
            all_results: 列表，每个元素是(主题, 该主题的检索结果)
        
        Returns:
            合并后的结果字典，包含主题匹配信息
        """
        print(f"\n🔄 开始合并 {len(all_results)} 个主题的检索结果...")
        
        # 导入V90主题匹配器用于排除词检查
        from .theme_matcher_v90 import get_theme_matcher_v90
        theme_matcher_v90 = get_theme_matcher_v90()
        
        # V47.0改进：检测是否是对比查询
        is_comparison_query = False
        if len(all_results) >= 2:
            # 检查主题是否包含对比相关词汇
            themes = [theme for theme, _ in all_results]
            # 检查查询是否包含对比相关词汇
            if hasattr(self, '_current_query_features') and self._current_query_features:
                query = self._current_query_features.get('original_query', '')
                if '对比' in query or '比较' in query or '区别' in query or '联系' in query:
                    is_comparison_query = True
                    print(f"   🔍 V47.0检测到对比查询: {themes}")
            # 检查主题是否包含对比相关词汇
            elif any('对比' in theme or '比较' in theme or '区别' in theme or '联系' in theme for theme in themes):
                is_comparison_query = True
                print(f"   🔍 V47.0检测到对比查询: {themes}")
            # 检查是否是两个不同主题的对比
            elif len(themes) == 2:
                # 检查两个主题是否是不同的函数类型
                function_themes = ["指数函数", "对数函数", "三角函数", "二次函数", "幂函数", "一次函数"]
                if all(theme in function_themes for theme in themes):
                    is_comparison_query = True
                    print(f"   🔍 V48.0检测到函数对比查询: {themes}")
            # 检查是否是指数函数和对数函数的对比
            elif len(themes) == 2 and "指数函数" in themes and "对数函数" in themes:
                is_comparison_query = True
                print(f"   🔍 V48.0检测到指数函数和对数函数对比查询: {themes}")
        
        # 检测是否是函数性质主题查询（单调性、奇偶性、周期性）
        is_function_property_query = False
        function_property_themes = ["函数的单调性", "函数的奇偶性", "函数的周期性"]
        themes = [theme for theme, _ in all_results]
        if any(theme in function_property_themes for theme in themes):
            is_function_property_query = True
            print(f"   🔍 检测到函数性质主题查询: {themes}")
        
        # 用于去重的字典，key为唯一标识，value为资源信息
        seen_resources = {}
        
        # 合并后的结果
        merged = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        # 获取所有主题列表
        all_themes = [theme for theme, _ in all_results]
        print(f"   📋 所有查询主题: {all_themes}")
        
        for theme, theme_results in all_results:
            if not theme_results.get("documents") or not theme_results["documents"][0]:
                continue
            
            docs = theme_results["documents"][0]
            metas = theme_results["metadatas"][0]
            dists = theme_results["distances"][0]
            ids = theme_results.get("ids", [[]])[0] if theme_results.get("ids") else [f"{theme}_{i}" for i in range(len(docs))]
            
            print(f"   📊 主题 '{theme}' 检索到 {len(docs)} 个结果")
            
            # 打印距离统计信息
            if len(dists) > 0:
                min_dist = min(dists)
                max_dist = max(dists)
                avg_dist = sum(dists) / len(dists)
                print(f"      📏 距离统计: 最小={min_dist:.4f}, 最大={max_dist:.4f}, 平均={avg_dist:.4f}")
                # 打印前5条结果的距离
                for i in range(min(5, len(dists))):
                    title = metas[i].get('title', '未知')[:30]
                    print(f"         - {title}... 距离={dists[i]:.4f}")
            
            for i, (doc, meta, dist, id_) in enumerate(zip(docs, metas, dists, ids)):
                # 生成唯一标识
                unique_key = f"{meta.get('source_file', '')}_{meta.get('title', '')}"
                
                # 只有相似度大于阈值的资源才被视为匹配该主题
                # 这里的dist是距离，距离越小表示相似度越高
                # 所以我们应该检查距离是否小于阈值
                # V16.1改进：进一步降低阈值，允许更多资源通过
                # 对于多主题查询，应该更加宽松，因为资源可能只匹配其中一个主题
                # V47.0改进：对比查询使用更宽松的阈值
                # V51.0改进：应用题和生活应用查询使用更宽松的阈值
                # V61.0改进：函数性质主题查询使用更宽松的阈值
                # V62.0改进：课件资源使用更宽松的阈值
                # V63.0改进：教案资源使用更宽松的阈值
                # V100.0改进：多主题查询时，使用更严格的阈值，确保每个主题的资源都足够相关
                resource_type = meta.get('resource_type', '')
                
                # 动态计算阈值：基于主题数量和查询类型
                num_themes = len(all_themes)
                
                if resource_type == 'courseware':
                    base_threshold = 2.5  # 课件资源使用更宽松的阈值
                    print(f"   🔍 V62.0课件资源：使用宽松阈值 {base_threshold}")
                elif resource_type == 'lesson_plan':
                    base_threshold = 2.5  # 教案资源使用更宽松的阈值
                    print(f"   🔍 V63.0教案资源：使用宽松阈值 {base_threshold}")
                elif is_comparison_query:
                    base_threshold = 1.5  # 对比查询使用更宽松的阈值
                    print(f"   🔍 V47.0对比查询：使用宽松阈值 {base_threshold}")
                elif '应用' in theme or '实际' in theme or '生活' in theme:
                    base_threshold = 1.8  # 应用题和生活应用查询使用更宽松的阈值
                    print(f"   🔍 V51.0应用题查询：使用宽松阈值 {base_threshold}")
                elif is_function_property_query:
                    # V100.0改进：函数性质查询，根据主题数量动态调整阈值
                    # 当多个函数性质主题时，使用更严格的阈值
                    if num_themes > 1:
                        base_threshold = 1.0  # 多主题函数性质查询使用更严格的阈值
                        print(f"   🔍 V100.0多主题函数性质查询：使用严格阈值 {base_threshold}")
                    else:
                        base_threshold = 1.5  # 单主题函数性质查询使用较宽松的阈值
                        print(f"   🔍 函数性质查询：使用阈值 {base_threshold}")
                else:
                    # V100.0改进：多主题查询时，使用更严格的阈值
                    if num_themes > 1:
                        base_threshold = 0.9  # 多主题查询使用更严格的阈值
                        print(f"   🔍 V100.0多主题查询：使用严格阈值 {base_threshold}")
                    else:
                        base_threshold = 1.0  # 正常查询的阈值
                
                similarity_threshold = base_threshold
                if dist < similarity_threshold:
                    # 关键修复：进行排除词检查
                    # 对于习题资源，跳过排除词检查，因为习题资源可能包含多个主题的关键词
                    resource_type = meta.get('resource_type', '')
                    if resource_type != 'exercise':
                        exclusion_factor = theme_matcher_v90._calculate_exclusion_factor(
                            theme, 
                            meta.get("title", ""), 
                            doc,
                            all_themes
                        )
                        if exclusion_factor == 0.0:
                            # 包含排除词，跳过此资源
                            print(f"      ⚠️ 排除：'{meta.get('title', '未知')}' 包含排除词 (主题: {theme})")
                            continue
                    else:
                        # 习题资源也需要进行排除词检查，确保只返回与查询主题相关的习题
                        # V17.0改进：为习题资源添加排除词检查
                        # V100.0改进：对于函数性质主题，不再跳过排除词检查，确保资源相关性
                        exclusion_factor = theme_matcher_v90._calculate_exclusion_factor(
                            theme, 
                            meta.get("title", ""), 
                            doc,
                            all_themes
                        )
                        if exclusion_factor == 0.0:
                            # 包含排除词，跳过此资源
                            print(f"      ⚠️ 排除：'{meta.get('title', '未知')}' 包含排除词 (主题: {theme})")
                            continue
                        else:
                            print(f"      ✅ 习题资源通过排除词检查: '{meta.get('title', '未知')}' (主题: {theme})")
                    
                    if unique_key not in seen_resources:
                        # 新资源，初始化
                        seen_resources[unique_key] = {
                            "doc": doc,
                            "meta": meta,
                            "dist": dist,
                            "id": id_,
                            "matched_themes": [theme],  # 记录匹配的主题
                            "theme_distances": {theme: dist}  # 记录与各主题的距离
                        }
                        print(f"      ✅ 新资源 '{meta.get('title', '未知')}' 匹配主题 '{theme}' (距离: {dist:.3f})")
                    else:
                        # 已存在的资源，添加主题匹配信息
                        if theme not in seen_resources[unique_key]["matched_themes"]:
                            # 对于多主题检索，只有距离小于阈值（相似度足够高），才添加主题匹配
                            # V61.0改进：对于函数性质主题，使用更宽松的阈值
                            if is_function_property_query:
                                similarity_threshold = 1.0  # 函数性质主题使用更宽松的阈值
                            else:
                                similarity_threshold = 0.7  # 距离阈值（从0.5提高到0.7）
                            if dist < similarity_threshold:
                                seen_resources[unique_key]["matched_themes"].append(theme)
                                seen_resources[unique_key]["theme_distances"][theme] = dist
                                print(f"      ➕ 资源 '{meta.get('title', '未知')}' 新增匹配主题 '{theme}' (距离: {dist:.3f})")
                            else:
                                print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 与主题 '{theme}' 相似度不足 (距离: {dist:.3f} >= {similarity_threshold})，不添加匹配")
                        else:
                            print(f"      ⚠️ 资源 '{meta.get('title', '未知')}' 已匹配主题 '{theme}'")
                        
                        # 确保元数据完整，特别是resource_type和title字段
                        existing_meta = seen_resources[unique_key]["meta"]
                        if "resource_type" not in existing_meta and "resource_type" in meta:
                            existing_meta["resource_type"] = meta["resource_type"]
                        if "title" not in existing_meta or not existing_meta["title"]:
                            if "title" in meta and meta["title"]:
                                existing_meta["title"] = meta["title"]
                        if "source_file" not in existing_meta or not existing_meta["source_file"]:
                            if "source_file" in meta and meta["source_file"]:
                                existing_meta["source_file"] = meta["source_file"]
        
        # 将资源信息转换为合并结果格式
        # V54.2改进：添加关键词匹配权重，提高教案资源的排名
        # 对于教案资源，如果标题包含查询主题的关键词，则提高排名
        def calculate_keyword_match_score(resource):
            """计算关键词匹配分数"""
            meta = resource["meta"]
            resource_type = meta.get('resource_type', '')
            title = meta.get('title', '')
            doc = resource["doc"]
            
            # 只对教案资源进行关键词匹配
            if resource_type != 'lesson_plan':
                return 0.0
            
            # 提取查询主题的关键词
            query_keywords = []
            for theme in all_themes:
                # 提取主题中的关键词
                if '函数' in theme:
                    query_keywords.append(theme)
                    # 提取函数类型
                    if '二次' in theme:
                        query_keywords.append('二次函数')
                    elif '三角' in theme:
                        query_keywords.append('三角函数')
                    elif '指数' in theme:
                        query_keywords.append('指数函数')
                    elif '对数' in theme:
                        query_keywords.append('对数函数')
                    elif '幂' in theme:
                        query_keywords.append('幂函数')
                    elif '一次' in theme:
                        query_keywords.append('一次函数')
            
            # 检查标题是否包含查询关键词
            keyword_match_score = 0.0
            for keyword in query_keywords:
                if keyword in title:
                    keyword_match_score += 0.3  # 标题匹配加分
                if keyword in doc:
                    keyword_match_score += 0.1  # 内容匹配加分
            
            return keyword_match_score
        
        # 按匹配主题数量降序排列，匹配主题数量相同时按平均距离排序
        sorted_resources = sorted(
            seen_resources.values(),
            key=lambda x: (
                -len(x["matched_themes"]),  # 匹配主题数量降序
                sum(x["theme_distances"].values()) / len(x["theme_distances"]) - calculate_keyword_match_score(x)  # 平均距离减去关键词匹配分数
            )
        )
        
        # 过滤资源，确保它们确实与主题相关
        # V13.1改进：暂时禁用LLM验证，只使用相似度阈值过滤
        filtered_resources = []
        print(f"\n🔍 开始过滤资源...")
        for resource in sorted_resources:
            # 检查相似度是否足够高
            # 这里的distance是距离，距离越小表示相似度越高
            # 所以我们应该检查距离是否小于阈值
            min_distance = min(resource["theme_distances"].values())
            # V16.1改进：进一步降低阈值，允许更多资源通过
            # 对于多主题查询，应该更加宽松，因为资源可能只匹配其中一个主题
            # V33.0改进：对于"还要多一点"的查询，使用更宽松的阈值
            # V47.0改进：对比查询使用更宽松的阈值
            # V48.0改进：根据查询类型和上下文动态调整阈值
            # V51.0改进：应用题和生活应用查询使用更宽松的阈值
            # V62.0改进：课件资源使用更宽松的阈值
            resource_type = resource['meta'].get('resource_type', '')
            if hasattr(self, '_loose_mode') and self._loose_mode:
                strict_threshold = 2.0  # 更宽松的阈值
                print(f"      🔍 V33.0宽松模式：使用阈值 {strict_threshold}")
            elif resource_type == 'courseware':
                strict_threshold = 2.5  # 课件资源使用更宽松的阈值
                print(f"      🔍 V62.0课件资源：使用宽松阈值 {strict_threshold}")
            elif is_comparison_query:
                strict_threshold = 2.0  # 对比查询使用更宽松的阈值
                print(f"      🔍 V47.0对比查询：使用宽松阈值 {strict_threshold}")
            elif any('应用' in theme or '实际' in theme or '生活' in theme for theme in resource["matched_themes"]):
                strict_threshold = 2.0  # 应用题和生活应用查询使用更宽松的阈值
                print(f"      🔍 V51.0应用题查询：使用宽松阈值 {strict_threshold}")
            elif len(resource["matched_themes"]) > 1:
                strict_threshold = 1.8  # 多主题匹配的资源使用较宽松的阈值
                print(f"      🔍 V48.0多主题匹配：使用宽松阈值 {strict_threshold}")
            else:
                strict_threshold = 1.5  # 正常阈值
            if min_distance > strict_threshold:
                print(f"      ⚠️ 过滤：'{resource['meta'].get('title', '未知')}' 相似度过低 (距离: {min_distance:.3f} > {strict_threshold})")
                continue
            
            # V33.0改进：年级筛选
            if self._current_grade_info:
                if not self._check_grade_match(resource['meta'], self._current_grade_info):
                    print(f"      ⚠️ 年级筛选：'{resource['meta'].get('title', '未知')}' 不符合年级要求 {self._current_grade_info}")
                    continue
            
            # 保留资源
            filtered_resources.append(resource)
            print(f"      ✅ 保留：'{resource['meta'].get('title', '未知')}' (匹配主题: {resource['matched_themes']})")
        
        print(f"✅ 过滤完成，保留 {len(filtered_resources)} 条相关结果")
        
        for resource in filtered_resources:
            merged["documents"][0].append(resource["doc"])
            # 在元数据中注入主题匹配信息
            meta_with_themes = resource["meta"].copy()
            meta_with_themes["_matched_themes"] = resource["matched_themes"]
            meta_with_themes["_theme_distances"] = resource["theme_distances"]
            meta_with_themes["_matched_theme_count"] = len(resource["matched_themes"])
            merged["metadatas"][0].append(meta_with_themes)
            merged["distances"][0].append(resource["dist"])
            merged["ids"][0].append(resource["id"])
        
        print(f"✅ 合并完成，共 {len(merged['documents'][0])} 条唯一结果")
        
        # V33.0改进：应用数量限制
        if self._current_quantity_limit:
            print(f"🔍 应用数量限制：{self._current_quantity_limit} 条结果")
            # 对每个结果列表应用数量限制
            for key in merged:
                if isinstance(merged[key], list) and merged[key]:
                    merged[key][0] = merged[key][0][:self._current_quantity_limit]
            print(f"✅ 数量限制应用完成，保留 {len(merged['documents'][0])} 条结果")
        
        # 打印多主题匹配的资源信息
        multi_theme_resources = [r for r in filtered_resources if len(r["matched_themes"]) > 1]
        if multi_theme_resources:
            print(f"   ⭐ 发现 {len(multi_theme_resources)} 条多主题匹配资源:")
            for r in multi_theme_resources[:5]:  # 只显示前5条
                title = r["meta"].get("title", "未知标题")
                themes = r["matched_themes"]
                print(f"      - {title}: 匹配主题 {themes}")
        
        # 打印单主题匹配的资源信息
        single_theme_resources = [r for r in filtered_resources if len(r["matched_themes"]) == 1]
        if single_theme_resources:
            print(f"   📋 发现 {len(single_theme_resources)} 条单主题匹配资源:")
            for r in single_theme_resources[:5]:  # 只显示前5条
                title = r["meta"].get("title", "未知标题")
                theme = r["matched_themes"][0]
                distance = r["theme_distances"][theme]
                print(f"      - {title}: 匹配主题 {theme} (距离: {distance:.4f})")
        
        return merged
    
    def _check_theme_relevance_with_llm(self, theme: str, doc: str, meta: Dict[str, Any]) -> bool:
        """
        使用LLM动态判断资源是否与主题相关
        
        Args:
            theme: 主题名称
            doc: 资源内容
            meta: 资源元数据
        
        Returns:
            是否相关
        """
        try:
            # 获取模型
            model = model_config.get_model("intent")
            
            # 构建提示词 - V13.0：更灵活的主题判断
            prompt = ChatPromptTemplate.from_template("""
你是一个数学教育资源评估专家。请判断以下资源是否与指定主题相关。

主题：{theme}

资源信息：
- 标题：{title}
- 内容摘要：{content}
- 知识点：{knowledge_points}

请判断该资源是否与主题"{theme}"相关。

主题定义：
- **指数函数**：形如 $y = a^x$（$a>0$ 且 $a \neq 1$）的函数，涉及指数运算、指数增长/衰减、指数方程/不等式
- **对数函数**：形如 $y = \log_a x$（$a>0$ 且 $a \neq 1$）的函数，涉及对数运算、对数方程/不等式
- **幂函数**：形如 $y = x^a$ 的函数，涉及幂运算
- **二次函数**：形如 $y = ax^2 + bx + c$（$a \neq 0$）的函数，涉及抛物线、顶点、对称轴
- **三角函数**：涉及 sin、cos、tan 等三角函数
- **三角恒等变换**：涉及三角函数的恒等变形，如诱导公式、和角公式、差角公式、二倍角公式等

判断标准：
1. 资源的主要内容是否明确涉及该主题的核心概念和方法
2. 资源是否包含该主题的典型特征和关键词
3. 资源是否属于该主题的知识体系

排除标准：
- 如果资源只涉及函数的基本概念（如定义域、值域、单调性、奇偶性）而没有特定主题的内容，判断为**不相关**
- 如果资源涉及的是正比例函数、反比例函数、一次函数等初等函数，判断为**不相关**
- 如果资源的主要内容和知识点与目标主题完全无关，判断为**不相关**

注意：
- 资源中可能包含多个主题的内容，只要主要内容涉及目标主题，就应该判断为**相关**
- 不要因为资源中包含其他主题的关键词就判断为**不相关**，除非这些关键词是主要内容

请只返回"相关"或"不相关"，不要返回其他内容。
""")
            
            # 提取资源信息
            title = meta.get("title", "未知标题")
            content = doc[:500] if len(doc) > 500 else doc  # 只取前500字符
            knowledge_points = meta.get("知识点", "")
            
            # 构建链
            chain = prompt | model | StrOutputParser()
            
            # 调用LLM
            result = chain.invoke({
                "theme": theme,
                "title": title,
                "content": content,
                "knowledge_points": knowledge_points
            })
            
            # 解析结果
            result = result.strip()
            is_relevant = "相关" in result
            
            print(f"      🔍 LLM判断：'{title}' 与主题 '{theme}' -> {result}")
            
            return is_relevant
            
        except Exception as e:
            print(f"      ⚠️ LLM判断失败: {e}，默认不相关")
            # 如果LLM判断失败，默认不相关，避免误匹配
            return False
    
    def _check_grade_match(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> bool:
        """
        V33.0: 检查资源是否符合年级要求
        
        V92.0改进：优化年级匹配逻辑
        - 高一高二：年级词不重要，重点在于知识点匹配
        - 高三：比较重要，因为高三主要是复习巩固而不是学新知
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息字典
            
        Returns:
            是否符合年级要求
        """
        try:
            # 从元数据中获取年级信息
            source_file = metadata.get('source_file', '')
            
            # 使用年级元数据丰富器推断年级
            grade = self.grade_enricher.infer_grade_from_path(source_file)
            if not grade:
                # 无法推断年级，默认通过
                return True
            
            # 检查年级是否匹配
            target_grade = grade_info.get('grade', '')
            if not target_grade:
                return True
            
            # V92.0改进：区分高一高二和高三的处理逻辑
            # 高一高二：年级词不重要，重点在于知识点匹配
            # 高三：比较重要，因为高三主要是复习巩固而不是学新知
            if target_grade in ["高一", "高二"]:
                # V92.0改进：对于高一高二，年级匹配非常宽松
                # 只要资源是高中内容就允许匹配，主要关注知识点匹配
                resource_grade = grade.get('grade', '')
                if any(g in resource_grade for g in ["高一", "高二", "高三"]):
                    print(f"      🎓 V92.0高一高二宽松匹配: 允许查看{grade.get('grade')}的内容（重点在知识点）")
                    return True
                return False
            
            elif target_grade == "高三":
                # V92.0改进：对于高三，年级匹配比较严格
                # 因为高三主要是复习巩固，需要更符合年级要求
                resource_grade = grade.get('grade', '')
                
                # 高三可以匹配所有高中年级的内容（复习性质）
                if "高三" in resource_grade:
                    return True
                elif "高二" in resource_grade:
                    print(f"      🎓 V92.0高三复习匹配: 允许查看高二的内容（复习巩固）")
                    return True
                elif "高一" in resource_grade:
                    print(f"      🎓 V92.0高三复习匹配: 允许查看高一的内容（基础复习）")
                    return True
                else:
                    return False
            
            # 其他情况：使用原来的逻辑
            # V53.1改进：检查是否是跨年级主题的查询
            # 某些主题（如函数、概率、立体几何等）在高中各年级都有学习，允许更宽松的年级匹配
            is_cross_grade_topic = False
            knowledge_tags = metadata.get('知识点标签', '')
            title = metadata.get('title', '')
            content = metadata.get('题干', '') + metadata.get('解析', '')
            
            # V53.1改进：使用动态生成的主题关键词，而不是硬编码
            # 这样当资源库扩展时，系统也能自动适应
            for keyword in self.all_theme_keywords:
                if keyword in knowledge_tags or keyword in title or keyword in content:
                    is_cross_grade_topic = True
                    break
            
            # 对于跨年级主题，允许更宽松的年级匹配
            if is_cross_grade_topic:
                # 跨年级主题允许相差2个级别（如高一和高二）
                resource_grade_level = grade.get('grade_level')
                target_grade_level = grade_info.get('grade_level')
                if resource_grade_level and target_grade_level:
                    level_diff = abs(resource_grade_level - target_grade_level)
                    if level_diff <= 2:
                        print(f"      🎓 跨年级主题: 允许查看{grade.get('grade')}的内容")
                        return True
                # 如果无法获取年级级别，只要是高中年级就允许匹配
                else:
                    resource_grade = grade.get('grade', '')
                    if "高一" in resource_grade or "高二" in resource_grade or "高三" in resource_grade:
                        print(f"      🎓 跨年级主题: 允许查看{grade.get('grade')}的内容")
                        return True
            
            # 年级匹配逻辑
            # 支持模糊匹配，如"高一"匹配"高一上学期"、"高一下学期"
            if target_grade in grade.get('grade', ''):
                return True
            
            # 特殊处理："高二"匹配"高二上学期"、"高二下学期"
            if target_grade == "高二" and ("高二" in grade.get('grade', '')):
                return True
            
            # 特殊处理："高三"匹配所有高中年级
            if target_grade == "高三":
                resource_grade = grade.get('grade', '')
                return "高一" in resource_grade or "高二" in resource_grade or "高三" in resource_grade
            
            # 特殊处理：高中年级之间的宽松匹配
            if any(target_grade in g for g in ["高一", "高二", "高三"]):
                resource_grade = grade.get('grade', '')
                if any(g in resource_grade for g in ["高一", "高二", "高三"]):
                    print(f"      🎓 高中年级宽松匹配: 允许查看{grade.get('grade')}的内容")
                    return True
            
            return False
        except Exception as e:
            print(f"      ⚠️ 年级匹配失败: {e}")
            # 年级匹配失败时默认通过，避免过度过滤
            return True
    
    def _check_knowledge_point_consistency(self, metadata: Dict[str, Any], core_theme: str, doc: str = "", query: str = "", relevance: float = 0.0) -> bool:
        """
        V15.0: 检查习题的知识点是否与查询要求一致
        
        当用户查询具体知识点（如"二次函数"）时，确保返回的习题属于该知识点，
        而不是其他相关知识点（如"三角函数"、"指数函数"等）
        
        Args:
            metadata: 习题元数据
            core_theme: 核心主题
            doc: 习题内容（V25.0添加）
            query: 用户原始查询（V46.2添加）
            relevance: 资源相关性分数（V96.0添加）
            
        Returns:
            是否一致
        """
        if not core_theme:
            return True
        
        # 解析核心主题，获取具体知识点
        themes = [t.strip() for t in core_theme.split(",") if t.strip()]
        
        # 调试信息
        print(f"\n   🔍 知识点一致性检查 - core_theme: '{core_theme}'")
        print(f"   🔍 解析出的主题: {themes}")
        print(f"   🔍 查询: '{query}'")
        print(f"   🔍 相关性: {relevance}")
        
        # 提取资源信息
        source_file = metadata.get('source_file', '')
        title = metadata.get('title', '')
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '') or metadata.get('knowledge_tags', '')
        question_content = metadata.get('题目描述', '') + metadata.get('题干', '') + metadata.get('content', '') + doc
        question_file = metadata.get('题目文件名', '')
        difficulty = metadata.get('难度（1-5）', '') or metadata.get('难度', '')
        analysis = metadata.get('解析', '')
        usage_scene = metadata.get('适用场景', '')
        all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content} {difficulty} {analysis} {usage_scene}"
        
        # 1. 对于高相关性资源，放宽过滤条件
        if relevance > 0.8:
            print(f"   ✅ 高相关性资源：相关性分数{relevance}，放宽过滤条件")
            return True
        
        # 2. 检查是否是通用函数性质主题
        general_function_properties = ["函数的单调性", "函数的奇偶性", "函数的周期性", "函数的值域", "函数的定义域", "函数的图像", "函数的性质", "函数概念", "函数的概念", "函数的应用"]
        is_general_property = any(prop in core_theme for prop in general_function_properties)
        
        if is_general_property:
            print(f"   ✅ 通用函数性质: '{core_theme}' 适用于所有函数类型")
            return True
        
        # 3. 检查是否是主观词汇
        subjective_words = ["基础题", "难题", "冲刺", "提高", "简单", "中等", "综合", "基础", "提高题", "难题", "压轴题"]
        is_subjective_word = any(word in core_theme for word in subjective_words)
        
        if is_subjective_word:
            print(f"   ✅ 主观词汇: '{core_theme}' 是主观词汇，跳过严格匹配")
            return True
        
        # 4. 提取具体知识点
        specific_knowledge_points = []
        generic_themes = ["函数", "数学", "教学", "函数的应用", "高中数学", "数学教学"]
        
        for theme in themes:
            if theme not in generic_themes:
                specific_knowledge_points.append(theme)
        
        if not specific_knowledge_points:
            print(f"   📝 未识别到具体知识点，跳过严格过滤")
            return True
        
        # 5. 动态获取知识点层级结构
        knowledge_hierarchy = self.knowledge_hierarchy
        
        # 6. 路径冲突检测 - 基于知识点层级结构的动态检测
        if source_file:
            # 检查是否存在路径冲突
            conflict_detected = False
            
            # 定义通用章节列表，这些章节可能包含多个知识点
            general_chapters = ["函数的概念", "函数的应用", "函数性质", "函数图像", "函数基础", "数学基础", "代数基础", "几何基础"]
            
            # 检查是否是通用章节
            is_general_chapter = any(general in source_file for general in general_chapters)
            
            # 动态检查每个知识点的章节信息
            for kp in specific_knowledge_points:
                if kp in knowledge_hierarchy:
                    kp_info = knowledge_hierarchy[kp]
                    chapters = kp_info.get("chapters", [])
                    
                    # 检查资源是否在该知识点的章节中
                    if any(chapter in source_file for chapter in chapters):
                        print(f"   ✅ 章节匹配：资源在知识点'{kp}'的章节中")
                        return True
            
            # 检查是否在其他知识点的章节中
            for theme_name, theme_info in knowledge_hierarchy.items():
                if theme_name not in specific_knowledge_points:
                    chapters = theme_info.get("chapters", [])
                    if any(chapter in source_file for chapter in chapters):
                        # 检查是否是同一父主题
                        has_same_parent = False
                        # 检查是否是父子主题关系
                        is_parent_child = False
                        # 检查是否是兄弟主题关系
                        is_sibling = False
                        
                        for kp in specific_knowledge_points:
                            if kp in knowledge_hierarchy and theme_name in knowledge_hierarchy:
                                kp_parent = knowledge_hierarchy[kp].get("parent_topic")
                                theme_parent = knowledge_hierarchy[theme_name].get("parent_topic")
                                
                                # 检查是否是同一父主题
                                if kp_parent and theme_parent and kp_parent == theme_parent:
                                    has_same_parent = True
                                    is_sibling = True
                                    break
                                
                                # 检查是否是父子主题关系（kp是theme_name的父主题）
                                if kp_parent and kp_parent == theme_name:
                                    is_parent_child = True
                                    break
                                
                                # 检查是否是父子主题关系（theme_name是kp的父主题）
                                if theme_parent and theme_parent == kp:
                                    is_parent_child = True
                                    break
                        
                        # 对于通用章节，即使不是同一父主题，也不过滤
                        if is_general_chapter:
                            print(f"   ✅ 通用章节：'{source_file}' 可能包含多个知识点，跳过路径冲突检测")
                            continue
                        
                        # 对于父子主题或兄弟主题，不过滤
                        if has_same_parent or is_parent_child:
                            if is_sibling:
                                print(f"   ✅ 兄弟主题：'{theme_name}' 和查询主题{specific_knowledge_points} 属于同一父主题，不过滤")
                            elif is_parent_child:
                                print(f"   ✅ 父子主题：'{theme_name}' 和查询主题{specific_knowledge_points} 存在父子关系，不过滤")
                            continue
                        
                        # 对于高相关性资源，放宽路径冲突检测
                        if relevance > 0.7:
                            print(f"   ✅ 高相关性资源：相关性分数{relevance}，放宽路径冲突检测")
                            continue
                        
                        # 对于教案、课件等资源，放宽路径冲突检测
                        resource_type = metadata.get('resource_type', '')
                        if resource_type in ['lesson_plan', 'courseware', 'syllabus']:
                            print(f"   ✅ 教学资源：{resource_type} 类型资源，放宽路径冲突检测")
                            continue
                        
                        # 其他情况，认为存在路径冲突
                        print(f"   ⚠️ 路径冲突检测: 资源在'{theme_name}'章节，但查询主题是{specific_knowledge_points}")
                        conflict_detected = True
                        break
            
            if conflict_detected:
                return False
        
        # 7. 知识点匹配 - 多维度检查
        has_match = False
        
        # 检查每个具体知识点
        for kp in specific_knowledge_points:
            if kp in knowledge_hierarchy:
                kp_info = knowledge_hierarchy[kp]
                keywords = kp_info.get("keywords", [])
                
                # 7.1 检查知识点标签
                if knowledge_tags:
                    if kp in knowledge_tags:
                        print(f"   ✅ 知识点标签完全匹配：'{kp}'")
                        return True
                    for keyword in keywords:
                        if keyword in knowledge_tags:
                            print(f"   ✅ 知识点关键词匹配：'{keyword}'")
                            has_match = True
                            break
                
                # 7.2 检查来源文件
                if not has_match:
                    if kp in source_file:
                        print(f"   ✅ 来源文件匹配：'{kp}'")
                        has_match = True
                    else:
                        for keyword in keywords:
                            if keyword in source_file:
                                print(f"   ✅ 来源文件关键词匹配：'{keyword}'")
                                has_match = True
                                break
                
                # 7.3 检查标题
                if not has_match:
                    if kp in title:
                        print(f"   ✅ 标题匹配：'{kp}'")
                        has_match = True
                    else:
                        for keyword in keywords:
                            if keyword in title:
                                print(f"   ✅ 标题关键词匹配：'{keyword}'")
                                has_match = True
                                break
                
                # 7.4 检查题目内容
                if not has_match and question_content:
                    if kp in question_content:
                        print(f"   ✅ 题目内容匹配：'{kp}'")
                        has_match = True
                    else:
                        for keyword in keywords:
                            if keyword in question_content:
                                print(f"   ✅ 题目内容关键词匹配：'{keyword}'")
                                has_match = True
                                break
                
                # 7.5 检查题目文件名
                if not has_match and question_file:
                    if kp in question_file:
                        print(f"   ✅ 题目文件名匹配：'{kp}'")
                        has_match = True
                    else:
                        for keyword in keywords:
                            if keyword in question_file:
                                print(f"   ✅ 题目文件名关键词匹配：'{keyword}'")
                                has_match = True
                                break
                
                if has_match:
                    break
        
        # 8. 严格过滤 - 检查是否包含非查询主题
        if not has_match:
            # 检查是否包含非查询主题的关键词
            for theme_name, theme_info in knowledge_hierarchy.items():
                if theme_name not in specific_knowledge_points:
                    # 检查是否是同一父主题
                    same_parent = False
                    for kp in specific_knowledge_points:
                        if kp in knowledge_hierarchy and theme_name in knowledge_hierarchy:
                            kp_parent = knowledge_hierarchy[kp].get("parent_topic")
                            theme_parent = knowledge_hierarchy[theme_name].get("parent_topic")
                            if kp_parent and theme_parent and kp_parent == theme_parent:
                                same_parent = True
                                break
                    
                    if not same_parent:
                        keywords = theme_info.get("keywords", [])
                        core_keywords = [k for k in keywords if len(k) >= 2]
                        
                        # 检查是否包含非查询主题的核心关键词
                        for keyword in core_keywords:
                            if keyword in all_info:
                                print(f"   ⚠️ 核心关键词过滤：包含非查询主题 '{theme_name}' 的关键词 '{keyword}'")
                                return False
        
        # 9. 对于中高相关性资源，适当放宽条件
        if relevance > 0.6 and not has_match:
            print(f"   ✅ 中相关性资源：相关性分数{relevance}，放宽匹配条件")
            return True
        
        return has_match
        
        # 10. 增强：如果是组合查询，允许部分匹配
        if len(specific_knowledge_points) > 1:
            # 对于组合查询，只要匹配其中一个知识点即可
            for kp in specific_knowledge_points:
                if kp in knowledge_hierarchy:
                    kp_info = knowledge_hierarchy[kp]
                    # 检查是否有任何匹配
                    all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
                    for keyword in kp_info["keywords"]:
                        if keyword in all_info:
                            print(f"   ✅ V15.8组合查询匹配：'{keyword}' 在信息中")
                            return True
        
        # 11. V53.1改进：对于函数性质相关查询，放宽检查条件
        # 使用动态生成的函数相关主题列表
        function_property_themes = [theme for theme in self.all_themes if '函数的' in theme and ('单调' in theme or '奇偶' in theme or '周期' in theme or '对称' in theme)]
        if any(theme in specific_knowledge_points for theme in function_property_themes):
            # 对于函数性质查询，只要习题是关于函数的，就认为相关
            all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
            for keyword in self.all_theme_keywords:
                if keyword in all_info:
                    print(f"   ✅ V15.9函数性质匹配：'{keyword}' 在信息中")
                    return True
        
        # 12. V53.1改进：对于所有查询，如果习题来自相关章节，放宽检查
        # 使用动态生成的章节信息
        for theme in self.all_themes:
            theme_info = self.knowledge_hierarchy.get(theme, {})
            theme_chapters = theme_info.get('chapters', [])
            if any(chapter in source_file for chapter in theme_chapters):
                # 如果习题来自相关章节，且查询包含相关关键词，则认为相关
                all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
                for keyword in self.all_theme_keywords:
                    if keyword in all_info:
                        print(f"   ✅ V16.0章节匹配：'{keyword}' 在信息中")
                        return True
        
        # V17.0改进：对于组合查询（如"指数函数和对数函数"），增强检查逻辑
        # 确保习题确实包含至少一个查询主题的关键词
        if len(specific_knowledge_points) > 1:
            # 检查是否包含任何查询主题的关键词
            has_any_query_keyword = False
            for kp in specific_knowledge_points:
                if kp in knowledge_hierarchy:
                    kp_info = knowledge_hierarchy[kp]
                    all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
                    for keyword in kp_info["keywords"]:
                        if keyword in all_info:
                            has_any_query_keyword = True
                            break
                    if has_any_query_keyword:
                        break
            
            # 如果不包含任何查询主题的关键词，过滤掉
            if not has_any_query_keyword:
                print(f"   ⚠️ V17.0过滤：不包含任何查询主题的关键词")
                return False
        
        # V21.2改进：对于复合知识点的习题，判断核心知识点是否与查询主题匹配
        # 如果知识点标签包含多个知识点，检查第一个知识点（核心知识点）是否是查询主题
        print(f"   🔍 V21.2调试 - knowledge_tags: '{knowledge_tags}', specific_knowledge_points: {specific_knowledge_points}")
        if knowledge_tags and ";" in knowledge_tags:
            core_knowledge = knowledge_tags.split(";")[0].strip()
            print(f"   🔍 V21.2调试 - 核心知识点: '{core_knowledge}'")
            # 如果核心知识点不是查询主题，但查询主题在标签中，需要进一步判断
            if core_knowledge not in specific_knowledge_points:
                # 检查核心知识点是否是其他明确的数学主题
                all_math_themes = ["二次函数", "幂函数", "三角函数", "指数函数", "对数函数", "函数的零点", "一次函数", "集合", "不等式"]
                if core_knowledge in all_math_themes:
                    # 核心知识点是其他数学主题，过滤掉
                    print(f"   ⚠️ V21.2过滤：核心知识点 '{core_knowledge}' 不是查询主题 {specific_knowledge_points}")
                    return False
        
        # V17.1改进：对于指数函数和对数函数的组合查询，增强检查
        if "指数函数" in specific_knowledge_points and "对数函数" in specific_knowledge_points:
            # 检查是否包含指数函数或对数函数的关键词
            has_exponential_or_log_keyword = False
            exponential_keywords = ["指数函数", "指数增长", "指数衰减", "指数幂", "指数运算", "指数", "2^x", "a^x", "e^"]
            log_keywords = ["对数函数", "对数运算", "对数方程", "对数", "log", "ln", "换底公式"]
            
            all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
            for keyword in exponential_keywords + log_keywords:
                if keyword in all_info:
                    has_exponential_or_log_keyword = True
                    break
            
            if not has_exponential_or_log_keyword:
                print(f"   ⚠️ V17.1过滤：不包含指数函数或对数函数的关键词")
                return False
        
        # 新增：对于三角恒等变换主题，增强检查
        if "三角恒等变换" in specific_knowledge_points:
            # 检查是否包含三角恒等变换的关键词
            has_trig_identity_keyword = False
            trig_identity_keywords = ["三角恒等变换", "三角恒等式", "恒等变换", "和差化积", "积化和差", "二倍角", "半角公式", "sin", "cos", "tan", "诱导公式", "两角和与差", "三角公式", "和角公式", "差角公式"]
            
            all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
            for keyword in trig_identity_keywords:
                if keyword in all_info:
                    has_trig_identity_keyword = True
                    break
            
            if not has_trig_identity_keyword:
                print(f"   ⚠️ 三角恒等变换过滤：不包含三角恒等变换相关关键词")
                return False
        
        # 新增：对于导数主题，增强检查
        if "导数" in specific_knowledge_points:
            # 检查是否包含导数的关键词
            has_derivative_keyword = False
            derivative_keywords = ["导数", "导函数", "微分", "求导", "f'", "y'", "dy/dx", "导数的几何意义", "切线方程", "瞬时变化率", "导数应用", "极值", "最值", "单调性"]
            
            all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
            for keyword in derivative_keywords:
                if keyword in all_info:
                    has_derivative_keyword = True
                    break
            
            if not has_derivative_keyword:
                print(f"   ⚠️ 导数过滤：不包含导数相关关键词")
                return False
        
        # V18.1改进：对于二次函数和一次函数的组合查询，增强检查
        if "二次函数" in specific_knowledge_points and "一次函数" in specific_knowledge_points:
            # 检查是否包含二次函数或一次函数的关键词
            has_quadratic_or_linear_keyword = False
            quadratic_keywords = ["二次函数", "抛物线", "顶点", "对称轴", "一元二次方程", "一元二次不等式", "x²", "x^2", "二次"]
            linear_keywords = ["一次函数", "线性函数", "直线", "一次"]
            
            all_info = f"{knowledge_tags} {source_file} {title} {question_file} {question_content}"
            for keyword in quadratic_keywords + linear_keywords:
                if keyword in all_info:
                    has_quadratic_or_linear_keyword = True
                    break
            
            if not has_quadratic_or_linear_keyword:
                print(f"   ⚠️ V18.1过滤：不包含二次函数或一次函数的关键词")
                return False
        
        # V44.0改进：简化逻辑，避免过度过滤
        # 如果没有找到明确的非查询主题，则认为是一致的
        print(f"   ✅ V44.0默认通过：未找到明确的非查询主题，认为一致")
        return True
    
    def _classify_results(self, results: Dict[str, Any], resource_types: List[str] = None, core_theme: str = "", query: str = "", question_type: str = "", grade: str = "", difficulty: str = "", exam_form: str = "") -> Dict[str, Any]:
        """
        对检索结果进行分类
        
        Args:
            results: ChromaDB查询结果
            resource_types: 用户明确提到的资源类型列表（用于精准检索）
            core_theme: 核心主题
            query: 用户查询（V32.0新增）
        
        Returns:
            分类后的资源字典
        """
        # 获取查询特征（V9.2）
        query_features = getattr(self, '_current_query_features', {})
        
        # 初始化各类资源列表
        classified = {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "exercise_resources": [],
            "visualization_examples": [],
            "general_resources": [],
            "courseware_resources": [],
            "lesson_case_resources": [],
            "ggb_resources": [],
            "syllabus_resources": []
        }
        
        # 处理检索结果
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                # 获取元数据
                metadata = self._get_metadata(results, i)
                distance = self._get_distance(results, i)
                
                # 获取资源类型
                resource_type = metadata.get('resource_type', 'theory')
                
                # V19.5改进：根据source_file判断资源类型
                # 如果source_file包含"习题"，则认为是习题资源
                source_file = metadata.get('source_file', '')
                if '习题' in source_file and resource_type != 'exercise':
                    resource_type = 'exercise'
                    print(f"   🔍 V19.5调试 - 根据source_file判断为习题资源: '{source_file}'")
                # V53.6改进：根据source_file判断其他资源类型
                elif '教案' in source_file and resource_type != 'lesson_plan':
                    resource_type = 'lesson_plan'
                    print(f"   🔍 V53.6调试 - 根据source_file判断为教案资源: '{source_file}'")
                elif '教学大纲' in source_file and resource_type != 'syllabus':
                    resource_type = 'syllabus'
                    print(f"   🔍 V53.6调试 - 根据source_file判断为教学大纲资源: '{source_file}'")
                elif 'ggb' in source_file.lower() and resource_type != 'ggb':
                    resource_type = 'ggb'
                    print(f"   🔍 V53.6调试 - 根据source_file判断为GGB资源: '{source_file}'")
                # V85.0改进：根据source_file判断课件资源
                elif any(keyword in source_file for keyword in ['课件', 'PPT', '幻灯片', '演示文稿']) and resource_type != 'courseware':
                    resource_type = 'courseware'
                    print(f"   🔍 V85.0调试 - 根据source_file判断为课件资源: '{source_file}'")
                
                # V19.3调试：输出资源类型和标题
                print(f"   🔍 V19.3调试 - 资源类型: '{resource_type}', 标题: '{metadata.get('title', '未知')}'")
                
                # 如果用户明确指定了资源类型，只保留匹配的类型
                # 特殊处理：如果用户指定了"资料"、"资源"、"教学资源"或"教学资料"，则保留所有资源
                # 或者如果映射后的标准类型是"资料"，也保留所有资源
                standard_types = [get_standard_name(rt) for rt in resource_types] if resource_types else []
                print(f"   🔍 V53.7调试 - resource_types: {resource_types}, standard_types: {standard_types}")
                if resource_types and not any(rt in ["资料", "资源", "教学资源", "教学资料"] for rt in resource_types) and not any(st == "资料" for st in standard_types):
                    # 使用统一的资源类型映射
                    matched = False
                    # 收集所有映射后的数据库类型
                    mapped_db_types = []
                    for user_type in resource_types:
                        mapped_db_type = get_db_type(user_type)
                        if mapped_db_type:
                            mapped_db_types.append(mapped_db_type)
                    print(f"   🔍 V73.0调试 - 映射后的数据库类型: {mapped_db_types}")
                    # 检查资源类型是否在映射后的数据库类型列表中
                    # V80.0改进：同时检查资源类型和用户输入的资源类型，以处理资源元数据中资源类型不一致的情况
                    resource_type_matched = False
                    for user_type in resource_types:
                        # 获取资源类型映射信息
                        mapping = get_resource_type_mapping(user_type)
                        if mapping:
                            standard_name = mapping[0]
                            db_type = mapping[1]
                            # 检查资源类型是否等于映射后的数据库类型
                            if resource_type == db_type:
                                resource_type_matched = True
                                print(f"   ✅ V80.0调试 - 资源类型匹配: {resource_type} 等于映射后的数据库类型 {db_type}")
                                break
                            # 检查资源类型是否等于用户输入的资源类型
                            elif resource_type == user_type:
                                resource_type_matched = True
                                print(f"   ✅ V80.0调试 - 资源类型匹配: {resource_type} 等于用户输入的资源类型 {user_type}")
                                break
                            # 检查资源类型是否等于标准名称
                            elif resource_type == standard_name:
                                resource_type_matched = True
                                print(f"   ✅ V82.0调试 - 资源类型匹配: {resource_type} 等于标准名称 {standard_name}")
                                break
                            # V86.0改进：对于课件和教案资源，增加更多的匹配方式
                            elif any(keyword in user_type for keyword in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"]) and resource_type == 'courseware':
                                resource_type_matched = True
                                print(f"   ✅ V86.0调试 - 课件资源类型匹配: {resource_type} 等于courseware")
                                break
                            elif any(keyword in user_type for keyword in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"]) and resource_type == 'lesson_plan':
                                resource_type_matched = True
                                print(f"   ✅ V86.0调试 - 教案资源类型匹配: {resource_type} 等于lesson_plan")
                                break
                            # V91.0改进：增加课例资源的匹配方式
                            elif any(keyword in user_type for keyword in ["课例", "教学视频", "课堂实录", "视频课"]) and resource_type == 'lesson_case':
                                resource_type_matched = True
                                print(f"   ✅ V91.0调试 - 课例资源类型匹配: {resource_type} 等于lesson_case")
                                break
                            # V91.0改进：增加GGB资源的匹配方式
                            elif any(keyword in user_type for keyword in ["GGB", "GeoGebra", "动态图", "可视化", "几何画板"]) and resource_type == 'ggb':
                                resource_type_matched = True
                                print(f"   ✅ V91.0调试 - GGB资源类型匹配: {resource_type} 等于ggb")
                                break
                            # V91.0改进：增加教学大纲资源的匹配方式
                            elif any(keyword in user_type for keyword in ["教学大纲", "大纲", "课程标准", "课程大纲"]) and resource_type == 'syllabus':
                                resource_type_matched = True
                                print(f"   ✅ V91.0调试 - 教学大纲资源类型匹配: {resource_type} 等于syllabus")
                                break
                            # V91.0改进：增加理论资源的匹配方式
                            elif any(keyword in user_type for keyword in ["理论", "知识点", "概念", "基础知识"]) and resource_type == 'theory':
                                resource_type_matched = True
                                print(f"   ✅ V91.0调试 - 理论资源类型匹配: {resource_type} 等于theory")
                                break
                            # V91.0改进：增加可视化资源的匹配方式
                            elif any(keyword in user_type for keyword in ["图像", "图形", "例子", "可视化", "图表"]) and resource_type == 'visualization':
                                resource_type_matched = True
                                print(f"   ✅ V91.0调试 - 可视化资源类型匹配: {resource_type} 等于visualization")
                                break
                    
                    if resource_type_matched:
                        matched = True
                    else:
                        print(f"   ⚠️ V80.0调试 - 资源类型不匹配: {resource_type} 不在映射后的数据库类型列表 {mapped_db_types} 中，也不等于用户输入的资源类型 {resource_types}")
                else:
                    matched = True
                    print(f"   ✅ V53.7调试 - 跳过资源类型过滤: resource_types为空或包含通用类型")
                
                # V71.0改进：如果用户指定了资源类型，但是没有匹配的资源，尝试不进行资源类型过滤
                if not matched and resource_types:
                    print(f"   📋 V71.0改进：没有匹配的资源类型，尝试不进行资源类型过滤")
                    matched = True
                
                # V96.0改进：根据资源可用性动态调整推荐策略
                # 1. 计算当前已收集的资源数量
                current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
                
                # 2. 计算相关性分数（距离越小，相关性越高）
                # 注意：这里的distance是向量相似度的距离，范围通常在0-2之间
                # 所以我们需要将其转换为0-1之间的相关性分数
                if distance is not None:
                    # 将距离转换为相关性分数，距离越小，相关性越高
                    # 距离为0时，相关性为1.0；距离为2时，相关性为0
                    relevance = max(0.0, 1.0 - (distance / 2))
                else:
                    relevance = 0.5
                
                # 3. 多维度相关性增强
                # 3.1 知识点匹配增强
                knowledge_match_score = 0.0
                knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '') or ''
                if core_theme and knowledge_tags:
                    # 检查核心主题是否在知识点标签中
                    themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                    for theme in themes:
                        if theme in knowledge_tags:
                            knowledge_match_score += 0.3
                            break
                    # 检查知识点标签是否包含核心主题的关键词
                    for theme in themes:
                        if theme in self.knowledge_hierarchy:
                            keywords = self.knowledge_hierarchy[theme].get("keywords", [])
                            for keyword in keywords:
                                if keyword in knowledge_tags:
                                    knowledge_match_score += 0.2
                                    break
                
                # 3.2 资源类型匹配增强
                type_match_score = 0.0
                if resource_types:
                    for user_type in resource_types:
                        mapping = get_resource_type_mapping(user_type)
                        if mapping:
                            standard_name = mapping[0]
                            db_type = mapping[1]
                            if resource_type == db_type or resource_type == user_type or resource_type == standard_name:
                                type_match_score = 0.2
                                break
                
                # 3.3 题目类型匹配增强（仅对习题资源）
                question_type_match_score = 0.0
                if resource_type == 'exercise' and question_type:
                    exercise_type = metadata.get('题目类型', '')
                    if exercise_type:
                        # 精确匹配或包含关系
                        if question_type in exercise_type or exercise_type in question_type:
                            question_type_match_score = 0.2
                        # 选择题特殊处理
                        elif question_type == '选择题' and any(option in doc for option in ['A.', 'B.', 'C.', 'D.', 'A、', 'B、', 'C、', 'D、']):
                            question_type_match_score = 0.15
                        # 证明题特殊处理
                        elif question_type == '证明题' and any(keyword in doc for keyword in ['求证', '证明', '证明题', '推导', '推导题']):
                            question_type_match_score = 0.15
                        # 解答题特殊处理
                        elif question_type == '解答题' and any(keyword in doc for keyword in ['解', '答案', '解析', '求', '计算']):
                            question_type_match_score = 0.15
                        # 填空题特殊处理
                        elif question_type == '填空题' and any(keyword in doc for keyword in ['__________', '______', '填空', '空']):
                            question_type_match_score = 0.15
                
                # 3.4 年级匹配增强
                grade_match_score = 0.0
                if grade:
                    resource_grade = metadata.get('grade', '') or metadata.get('年级', '')
                    if resource_grade:
                        # 精确匹配或包含关系
                        if grade in resource_grade or resource_grade in grade:
                            grade_match_score = 0.1
                        # 高三匹配所有高中年级
                        elif grade == "高三" and any(g in resource_grade for g in ["高一", "高二", "高三"]):
                            grade_match_score = 0.05
                        # 高中年级之间的宽松匹配
                        elif any(target_grade in grade for target_grade in ["高一", "高二", "高三"]) and any(g in resource_grade for g in ["高一", "高二", "高三"]):
                            grade_match_score = 0.05
                
                # 3.5 难度匹配增强
                difficulty_match_score = 0.0
                if difficulty:
                    resource_difficulty = metadata.get('difficulty', '') or metadata.get('难度', '') or metadata.get('难度（1-5）', '')
                    if resource_difficulty:
                        # 难度映射：资源难度 -> 标准难度
                        difficulty_map = {
                            '基础': ['基础', '简单', '入门', '初级', '1', '2'],
                            '中等': ['中等', '一般', '普通', '常见', '2', '3'],
                            '拔高': ['拔高', '难', '困难', '挑战', '压轴', '3', '4', '5']
                        }
                        for level, keywords in difficulty_map.items():
                            if difficulty == level:
                                if any(keyword in str(resource_difficulty) for keyword in keywords):
                                    difficulty_match_score = 0.1
                                    break
                
                # 4. 综合计算最终相关性分数
                # 基础相关性占60%，其他因素占40%
                final_relevance = relevance * 0.6 + (
                    knowledge_match_score + 
                    type_match_score + 
                    question_type_match_score + 
                    grade_match_score + 
                    difficulty_match_score
                ) * 0.4
                
                # 确保分数在0-1之间
                final_relevance = max(0.0, min(1.0, final_relevance))
                
                # 使用最终相关性分数
                relevance = final_relevance
                
                # 检查资源是否包含核心主题
                contains_core_theme = False
                if core_theme:
                    # 检查文档内容、标题和元数据是否包含核心主题
                    content = doc or ""
                    title = metadata.get('title', '') or ""
                    metadata_str = str(metadata) or ""
                    contains_core_theme = core_theme in content or core_theme in title or core_theme in metadata_str
                
                # 3. 对于高相关性资源或包含核心主题的资源，即使某些过滤条件不完全匹配，也应该保留
                if relevance > 0.3 or contains_core_theme:
                    print(f"   ✅ V96.0高相关性资源：相关性分数{relevance:.2f}，优先保留")
                    # 高相关性资源直接通过，跳过后续过滤
                    # 创建资源对象
                    resource = {
                        "title": metadata.get('title', '未知'),
                        "content": doc,
                        "source": metadata.get('source_file', ''),
                        "relevance": relevance,
                        "metadata": metadata,
                        "base_relevance": relevance,
                        "theme_match": False,
                        "type_match": False,
                        "matched_theme_count": 0,
                        "theme_boost": 0.0,
                        "conflict_theme": False,
                        "matched_themes": [],
                        "is_comprehensive": False,
                        "难度": metadata.get('难度', '') or metadata.get('difficulty', '') or metadata.get('难度（1-5）', ''),
                        "题目类型": metadata.get('题目类型', ''),
                        "知识点": metadata.get('知识点', '') or metadata.get('知识点标签', '')
                    }
                    # 将资源添加到分类结果中
                    # 映射资源类型到分类键
                    category_map = {
                        "lesson_plan": "lesson_plan_patterns",
                        "visualization": "visualization_examples",
                        "exercise": "exercise_resources",
                        "courseware": "courseware_resources",
                        "lesson_case": "lesson_case_resources",
                        "ggb": "ggb_resources",
                        "syllabus": "syllabus_resources",
                        "theory": "theory_resources"
                    }
                    category = category_map.get(resource_type, "theory_resources")
                    classified[category].append(resource)
                    # 跳过后续过滤
                    continue
                else:
                    # 4. 对于低相关性资源，进行严格过滤
                    pass
                
                # 题目类型过滤（V45.0改进：更灵活的题目类型匹配）
                if matched and resource_type == 'exercise' and question_type:
                    # 检查题目类型是否匹配
                    exercise_type = metadata.get('题目类型', '')
                    
                    # V45.0改进：更灵活的题目类型匹配策略
                    # 如果题目类型为空，不进行过滤
                    if not exercise_type:
                        print(f"   ✅ V45.0跳过题目类型过滤: 题目类型为空")
                        is_type_match = True
                    else:
                        # V45.0改进：题目类型模糊匹配，支持多种匹配方式
                        is_type_match = False
                        
                        # 1. 精确匹配或包含关系
                        if question_type in exercise_type or exercise_type in question_type:
                            is_type_match = True
                            print(f"   ✅ V45.0题目类型精确匹配: {question_type} 在 {exercise_type} 中")
                        
                        # 2. 对于选择题，检查是否包含选项标记或选择题相关关键词
                        elif question_type == '选择题':
                            # 检查是否包含选项标记
                            if any(option in doc for option in ['A.', 'B.', 'C.', 'D.', 'A、', 'B、', 'C、', 'D、']):
                                is_type_match = True
                                print(f"   ✅ V45.0选择题选项匹配: 发现选项标记")
                            # 检查题目类型是否包含"选择"关键词
                            elif '选择' in exercise_type:
                                is_type_match = True
                                print(f"   ✅ V45.0选择题类型匹配: 题目类型包含'选择'")
                            # V45.0改进：对于通用查询，不过滤
                            elif any(generic_word in query for generic_word in ['几道', '一些', '给我', '推荐', '有没有', '基础', '简单']):
                                is_type_match = True
                                print(f"   ✅ V45.0通用查询匹配: 查询包含通用词，跳过题目类型过滤")
                        
                        # 3. V46.0改进：对于证明题，检查是否包含证明相关关键词或解答题包含证明
                        elif question_type == '证明题':
                            # 检查是否包含证明相关关键词
                            if any(keyword in doc for keyword in ['求证', '证明', '证明题', '推导', '推导题']):
                                is_type_match = True
                                print(f"   ✅ V46.0证明题关键词匹配: 发现证明关键词")
                            # V46.0改进：解答题如果包含证明相关内容，也认为是证明题
                            elif '解答' in exercise_type and any(keyword in doc for keyword in ['证明', '单调性', '求证']):
                                is_type_match = True
                                print(f"   ✅ V46.0证明题匹配: 解答题包含证明内容")
                            # V46.0改进：对于证明题查询，放宽匹配条件
                            elif any(keyword in query for keyword in ['单调性', '证明']) and '解答' in exercise_type:
                                is_type_match = True
                                print(f"   ✅ V46.0证明题匹配: 查询包含证明相关词，解答题通过")
                            # V46.0改进：对于单调性证明题，检查知识点标签
                            elif '单调性' in query and '解答' in exercise_type:
                                knowledge_tags = metadata.get('知识点标签', '')
                                if any(keyword in knowledge_tags for keyword in ['单调性', '单调', '增函数', '减函数']):
                                    is_type_match = True
                                    print(f"   ✅ V46.0证明题匹配: 知识点标签'{knowledge_tags}'包含单调性相关关键词")
                            # V46.0改进：对于证明题查询，所有解答题都应该考虑
                            elif '解答' in exercise_type:
                                is_type_match = True
                                print(f"   ✅ V46.0证明题匹配: 解答题类型，放宽匹配条件")
                        
                        # 4. 对于解答题，检查是否包含解答相关特征
                        elif question_type == '解答题' and any(keyword in doc for keyword in ['解', '答案', '解析', '求', '计算']):
                            is_type_match = True
                            print(f"   ✅ V45.0解答题关键词匹配: 发现解答关键词")
                        
                        # 5. V45.0改进：如果查询包含"习题"、"题目"、"练习题"等通用词，不进行严格过滤
                        elif any(generic_word in query for generic_word in ['习题', '题目', '练习题', '测试题', '题']):
                            is_type_match = True
                            print(f"   ✅ V45.0通用查询匹配: 查询包含通用词，跳过题目类型过滤")
                        
                        # 6. V45.0改进：对于填空题，检查是否包含填空特征
                        elif question_type == '填空题' and any(keyword in doc for keyword in ['__________', '______', '填空', '空']):
                            is_type_match = True
                            print(f"   ✅ V45.0填空题特征匹配: 发现填空特征")
                        
                        # V95.0改进：对于应用题，检查是否包含应用相关特征
                        elif question_type == '应用题':
                            # 检查题目类型字段
                            if '应用' in exercise_type:
                                is_type_match = True
                                print(f"   ✅ V95.0应用题类型匹配: 题目类型包含'应用'")
                            # 检查内容是否包含应用场景
                            elif any(keyword in doc for keyword in ['实际', '应用', '问题', '情景', '情境', '生活', '生产', '经济', '物理', '化学']):
                                is_type_match = True
                                print(f"   ✅ V95.0应用题内容匹配: 发现应用相关关键词")
                            # 检查知识点标签
                            elif any(keyword in (metadata.get('知识点标签', '') or '') for keyword in ['应用', '实际']):
                                is_type_match = True
                                print(f"   ✅ V95.0应用题知识点匹配: 知识点标签包含应用相关词")
                            # 对于应用题查询，放宽匹配条件
                            elif '解答' in exercise_type or not exercise_type:
                                is_type_match = True
                                print(f"   ✅ V95.0应用题放宽匹配: 解答题或无类型标记")
                        
                        # V95.0改进：如果资源不足，放宽题目类型限制
                        if not is_type_match:
                            # 检查当前已收集的资源数量
                            current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
                            # 如果资源不足（少于5个），放宽题目类型限制
                            if current_count < 5:
                                print(f"   ✅ V95.0资源不足，放宽题目类型限制: 接受题目类型'{exercise_type}'")
                                is_type_match = True
                        
                        if not is_type_match:
                            print(f"   ⚠️ V45.0跳过不匹配的习题类型: {exercise_type} != {question_type}")
                            matched = False
                    
                # 如果不匹配，跳过这个资源
                if not matched:
                    continue
                
                # V15.0: 对习题资源进行知识点一致性检查
                if resource_type == 'exercise':
                    # 传递所有核心主题，而不是只传递第一个
                    is_consistent = self._check_knowledge_point_consistency(metadata, core_theme, doc, query, relevance)
                    if not is_consistent:
                        print(f"   ⚠️ V15.0跳过不一致的习题: '{metadata.get('title', '未知')}' (来源: {metadata.get('source_file', '')})")
                        continue
                
                # V49.0改进：多维度条件过滤
                if resource_type == 'exercise':
                    # 1. 年级过滤
                    # V62.0改进：与V94.0保持一致，高一高二查询禁用年级过滤
                    if grade and grade not in ['高一', '高二']:
                        resource_grade = metadata.get('grade', '') or metadata.get('年级', '')
                        if resource_grade:
                            # 支持模糊匹配，如"高一"匹配"高一上学期"、"高一下学期"
                            if grade not in resource_grade:
                                # V50.0改进：对于特定主题，放宽年级限制
                                # 三角函数通常在高一学习，所以高二查询也应该返回高一的三角函数题
                                is_math_topic = any(topic in doc.lower() for topic in ['三角函数', '正弦', '余弦', '正切', '诱导公式', '二倍角'])
                                
                                if is_math_topic and '高一' in resource_grade and '高二' in grade:
                                    # 对于三角函数主题，高二查询可以返回高一的题目
                                    print(f"   ✓ V50.0年级放宽: 三角函数主题，允许'高二'查询返回'高一'题目")
                                else:
                                    # 特殊处理：高三匹配所有高中年级
                                    if grade != "高三" or ("高一" not in resource_grade and "高二" not in resource_grade and "高三" not in resource_grade):
                                        print(f"   ⚠️ V49.0年级过滤: 资源年级'{resource_grade}'与查询年级'{grade}'不匹配")
                                        continue
                    elif grade and grade in ['高一', '高二']:
                        print(f"   ✓ V62.0高一高二查询: 禁用年级过滤，重点在知识点匹配")
                    
                    # 2. 难度过滤
                    if difficulty:
                        # 优先使用"难度（1-5）"字段
                        resource_difficulty = metadata.get('难度（1-5）', '')
                        if not resource_difficulty:
                            resource_difficulty = metadata.get('difficulty', '') or metadata.get('难度', '')
                        
                        if resource_difficulty:
                            # 难度映射：资源难度 -> 标准难度
                            difficulty_map = {
                                '基础': ['基础', '简单', '入门', '初级', '1', '2'],
                                '中等': ['中等', '一般', '普通', '常见', '3'],
                                '拔高': ['拔高', '难', '困难', '挑战', '压轴', '4', '5']
                            }
                            
                            # 检查资源难度是否匹配查询难度
                            is_difficulty_match = False
                            for level, keywords in difficulty_map.items():
                                if difficulty == level:
                                    if any(str(keyword) in str(resource_difficulty) for keyword in keywords):
                                        is_difficulty_match = True
                                        break
                            
                            # V95.0改进：如果资源不足，放宽难度限制
                            if not is_difficulty_match:
                                # 检查当前已收集的资源数量
                                current_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
                                # 如果资源不足（少于5个），放宽难度限制
                                if current_count < 5:
                                    print(f"   ✅ V95.0资源不足，放宽难度限制: 接受资源难度'{resource_difficulty}'")
                                    is_difficulty_match = True
                                else:
                                    print(f"   ⚠️ V49.0难度过滤: 资源难度'{resource_difficulty}'与查询难度'{difficulty}'不匹配")
                                    continue
                    
                    # 3. 考查形式过滤
                    if exam_form:
                        # 检查文档内容或知识点标签是否包含考查形式相关关键词
                        content = doc + (metadata.get('知识点', '') or '') + (metadata.get('知识点标签', '') or '')
                        
                        # V50.0改进：更精确的考查形式关键词
                        exam_form_keywords = {
                            '性质': ['性质', '单调性', '奇偶性', '周期性', '对称性', '定义域', '值域'],
                            '应用': ['应用', '实际应用', '应用题', '综合应用'],
                            '证明': ['证明', '证明题', '求证', '推导'],
                            '计算': ['计算', '计算题', '求解', '求值']
                        }
                        
                        # V50.0改进：区分不同类型的证明题
                        # 如果查询是"函数单调性证明"或"函数奇偶性证明"，需要排除三角恒等式证明
                        if ('单调性' in query and '证明' in query) or ('奇偶性' in query and '证明' in query):
                            # 检查是否是三角恒等式证明（应该排除）
                            # 三角恒等式证明的特点：证明等式关系，涉及恒等变换
                            is_trig_identity = (
                                '恒等' in content or 
                                ('求证' in content and '=' in content and any(trig in content for trig in ['sin', 'cos', 'tan']))
                            )
                            # 检查是否是真正的单调性或奇偶性证明（应该保留）
                            is_monotonicity_proof = any(keyword in content for keyword in ['单调性', '递增', '递减', '增函数', '减函数', '单调递增', '单调递减'])
                            is_parity_proof = any(keyword in content for keyword in ['奇偶性', '奇函数', '偶函数', '奇函数证明', '偶函数证明'])
                            
                            if is_trig_identity and not is_monotonicity_proof and not is_parity_proof:
                                print(f"   ⚠️ V50.0证明题过滤: 排除三角恒等式证明，需要单调性或奇偶性证明")
                                continue
                        
                        # 检查是否匹配
                        is_exam_form_match = False
                        for form, keywords in exam_form_keywords.items():
                            if exam_form == form:
                                if any(keyword in content for keyword in keywords):
                                    is_exam_form_match = True
                                    break
                        
                        # 如果内容为空或者没有匹配到，不过滤，保留资源
                        # if not is_exam_form_match:
                        #     print(f"   ⚠️ V49.0考查形式过滤: 资源内容与查询考查形式'{exam_form}'不匹配")
                        #     continue
                
                # 创建资源对象（使用V2主题匹配器，V32.0修复：传递query参数）
                # V87.0改进：对于课件和教案资源，确保资源类型正确映射
                if resource_type == 'courseware' and any(rt in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"] for rt in resource_types):
                    # 确保课件资源被正确分类
                    print(f"   ✅ V87.0调试 - 课件资源类型确认: {resource_type}")
                elif resource_type == 'lesson_plan' and any(rt in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"] for rt in resource_types):
                    # 确保教案资源被正确分类
                    print(f"   ✅ V87.0调试 - 教案资源类型确认: {resource_type}")
                
                resource = self._create_resource(doc, metadata, distance, resource_type, core_theme, resource_types, query, question_type)
                
                # V9.2：对习题资源应用内容匹配（难度、题目类型）
                if resource_type == 'exercise' and query_features.get('has_content_requirement'):
                    content_score = self.content_extractor.calculate_content_match_score(
                        {},  # 习题资源没有content_features
                        query_features,
                        metadata,  # 习题资源使用metadata
                        doc  # 传递文档内容作为resource_content
                    )
                    # 将内容匹配得分融入相关性
                    original_relevance = resource.get('relevance', 0)
                    
                    # 只有当基础相关性高于阈值时，才应用内容匹配得分
                    min_relevance_threshold = 0.30
                    if original_relevance >= min_relevance_threshold:
                        # 内容匹配得分占30%权重
                        resource['relevance'] = original_relevance * 0.7 + content_score * 0.3
                        resource['content_match_score'] = content_score
                        resource['original_relevance'] = original_relevance
                    else:
                        # 基础相关性过低，不应用内容匹配得分
                        resource['relevance'] = 0.0
                        resource['content_match_score'] = 0.0
                        resource['original_relevance'] = original_relevance
                        resource['should_show'] = False
                    
                    # V9.3：如果题目类型要求严格不匹配，跳过该资源
                    # V18.0改进：严格题目类型过滤，不再动态放宽，确保返回结果符合用户要求
                    # V18.4改进：无论content_score如何，只要题目类型不匹配就跳过
                    # V52.0改进：对于应用题查询，允许所有类型的习题
                    if query_features.get('required_exercise_type'):
                        # 检查题目类型是否匹配
                        exercise_type = metadata.get('题目类型', '')
                        required_type = query_features['required_exercise_type']
                        
                        # V52.0改进：对于应用题查询，允许所有类型的习题
                        if required_type == '应用题' or '应用' in query:
                            print(f"   ✅ V52.0应用题查询: 允许所有类型的习题")
                        else:
                            # V9.4：题目类型映射（计算题 -> 解答题）
                            mapped_type = required_type
                            if required_type == '计算题':
                                mapped_type = '解答题'
                            
                            # V38.0改进：题目类型模糊匹配，支持包含关系
                            # 例如：required_type="选择题"可以匹配"选择题(单选)"、"选择题(多选)"等
                            # 检查mapped_type是否在exercise_type中，或者exercise_type是否包含mapped_type
                            if exercise_type:
                                # V46.0改进：对于证明题，应用更灵活的匹配逻辑
                                if mapped_type == '证明题':
                                    # 检查是否包含证明相关关键词
                                    if any(keyword in doc for keyword in ['求证', '证明', '证明题', '推导', '推导题']):
                                        print(f"   ✅ V46.0证明题关键词匹配: 发现证明关键词")
                                    # V46.0改进：解答题如果包含证明相关内容，也认为是证明题
                                    elif '解答' in exercise_type and any(keyword in doc for keyword in ['证明', '单调性', '求证']):
                                        print(f"   ✅ V46.0证明题匹配: 解答题包含证明内容")
                                    # V46.0改进：对于证明题查询，放宽匹配条件
                                    elif any(keyword in query for keyword in ['单调性', '证明']) and '解答' in exercise_type:
                                        print(f"   ✅ V46.0证明题匹配: 查询包含证明相关词，解答题通过")
                                    # V46.0改进：对于单调性证明题，检查知识点标签
                                    elif '单调性' in query and '解答' in exercise_type:
                                        knowledge_tags = metadata.get('知识点标签', '')
                                        if any(keyword in knowledge_tags for keyword in ['单调性', '单调', '增函数', '减函数']):
                                            print(f"   ✅ V46.0证明题匹配: 知识点标签'{knowledge_tags}'包含单调性相关关键词")
                                    # V46.0改进：对于证明题查询，所有解答题都应该考虑
                                    elif '解答' in exercise_type:
                                        print(f"   ✅ V46.0证明题匹配: 解答题类型，放宽匹配条件")
                                    else:
                                        print(f"   ⚠️ V18.0/V18.4跳过不匹配的习题类型: {exercise_type} != {required_type} (映射为: {mapped_type})")
                                        continue
                                elif mapped_type not in exercise_type and exercise_type not in mapped_type:
                                    print(f"   ⚠️ V18.0/V18.4跳过不匹配的习题类型: {exercise_type} != {required_type} (映射为: {mapped_type})")
                                    continue
                                else:
                                    print(f"   ✅ V38.0题目类型模糊匹配: {mapped_type} 在 {exercise_type} 中")
                
                # V30.5修复：只有should_show为True时才添加资源
                if resource.get('should_show', True):
                    # V88.0改进：对于课件和教案资源，确保资源被添加到正确的分类中
                    if resource_type == 'courseware' and any(rt in ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"] for rt in resource_types):
                        # 确保课件资源被添加到courseware_resources分类中
                        print(f"   📊 V88.0分类调整 - 课件资源添加到courseware_resources")
                        self._add_to_category(classified, 'courseware', resource)
                    elif resource_type == 'lesson_plan' and any(rt in ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"] for rt in resource_types):
                        # 确保教案资源被添加到lesson_plan_patterns分类中
                        print(f"   📊 V88.0分类调整 - 教案资源添加到lesson_plan_patterns")
                        self._add_to_category(classified, 'lesson_plan', resource)
                    else:
                        # 动态分类
                        dynamic_category = self._dynamic_classify_resource(resource, doc, metadata, query)
                        if dynamic_category:
                            print(f"   📊 V33.0动态分类: {dynamic_category}")
                            self._add_to_category(classified, dynamic_category, resource)
                        else:
                            # 分类资源
                            self._add_to_category(classified, resource_type, resource)
                else:
                    print(f"   ⚠️ V30.5跳过should_show=False的资源: '{resource.get('title', '未知')}'")
        
        quantity_limit = getattr(self, '_current_quantity_limit', None)
        grade_info = getattr(self, '_current_grade_info', None)
        clarified_topic = getattr(self, '_current_clarified_topic', None)
        
        # V52.0改进：添加调试信息，显示年级过滤前的资源数量
        print(f"\n🔍 V52.0年级过滤前资源数量:")
        for category in classified:
            if isinstance(classified[category], list):
                print(f"   📊 {category}: {len(classified[category])} 条资源")
        
        if grade_info:
            print(f"\n🎓 V33.0应用年级过滤: {grade_info}")
            classified = self._apply_grade_filter(classified, grade_info, query)
        
        if clarified_topic and clarified_topic.get('should_exclude'):
            print(f"\n🔍 V33.0应用主题排除过滤: {clarified_topic}")
            classified = self._apply_topic_exclusion(classified, clarified_topic)
        
        if quantity_limit:
            print(f"\n📊 V33.0应用数量限制: {quantity_limit}")
            classified = self._apply_quantity_limit(classified, quantity_limit)
        
        # V95.0改进：如果所有分类都为空，尝试返回相关主题的资源
        total_resources = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
        if total_resources == 0:
            print(f"\n⚠️ V95.0资源不足，尝试返回相关主题资源")
            # 使用现有的vector_db_builder
            if hasattr(self, 'vector_db_builder'):
                client = self.vector_db_builder.get_chroma_client()
                collection = client.get_collection(name=self.COLLECTION_NAME)
                
                # 提取查询中的主题关键词
                from app.core.theme_matcher import ThemeMatcher
                theme_matcher = ThemeMatcher()
                detected_themes = theme_matcher.dynamic_theme_detection(query, query)
                
                if detected_themes:
                    # 使用第一个检测到的主题
                    main_theme = detected_themes[0]['theme']
                    print(f"   🔍 V95.0检测到主题: {main_theme}")
                    
                    # 查询相关主题的资源
                    results = collection.get(
                        where={"resource_type": "exercise"},
                        limit=20
                    )
                    
                    # 筛选包含主题关键词的资源
                    related_resources = []
                    for i, metadata in enumerate(results['metadatas']):
                        knowledge_tags = metadata.get('知识点标签', '')
                        source_file = metadata.get('source_file', '')
                        title = metadata.get('title', '')
                        
                        # 检查是否包含主题关键词
                        if main_theme in knowledge_tags or main_theme in source_file or main_theme in title:
                            related_resources.append({
                                'id': results['ids'][i],
                                'title': title,
                                'resource_type': 'exercise',
                                'relevance': 0.8,  # 设置一个较高的相关性分数
                                'knowledge_tags': knowledge_tags,
                                'source_file': source_file
                            })
                    
                    if related_resources:
                        print(f"   ✅ V95.0返回{main_theme}相关资源: {len(related_resources)}条")
                        classified['exercise_resources'] = related_resources[:5]  # 返回最多5条
                    else:
                        print(f"   ❌ V95.0未找到{main_theme}相关资源")
                else:
                    print(f"   ❌ V95.0未检测到主题")
            else:
                print(f"   ❌ V95.0无法获取vector_db_builder")
        
        return classified
    
    def _dynamic_classify_resource(self, resource: Dict[str, Any], content: str, metadata: Dict[str, Any], query: str) -> Optional[str]:
        """
        动态分类资源
        V54.0改进：添加对教学大纲和课例视频的支持
        
        Args:
            resource: 资源对象
            content: 资源内容
            metadata: 资源元数据
            query: 用户查询
        
        Returns:
            动态分类结果
        """
        # 1. 基于内容的动态分类
        if '教案' in content or '教学目标' in content or '教学过程' in content:
            return 'lesson_plan'
        elif '教学大纲' in content or '教学任务' in content:
            return 'syllabus'
        elif '课例' in content or '课堂实录' in content or '教学视频' in content:
            return 'lesson_case'
        elif '习题' in content or '题目' in content or '练习' in content or '选择题' in content or '填空题' in content or '解答题' in content:
            return 'exercise'
        elif '课件' in content or 'PPT' in content or '幻灯片' in content:
            return 'courseware'
        elif 'GeoGebra' in content or 'ggb' in content.lower() or '几何画板' in content:
            return 'ggb'
        elif '可视化' in content or '图表' in content or '图像' in content:
            return 'visualization'
        
        # 2. 基于元数据的动态分类
        source_file = metadata.get('source_file', '')
        if '教学大纲' in source_file:
            return 'syllabus'
        elif '教案' in source_file:
            return 'lesson_plan'
        elif '课例' in source_file:
            return 'lesson_case'
        elif '习题' in source_file:
            return 'exercise'
        elif '课件' in source_file:
            return 'courseware'
        elif 'ggb' in source_file.lower():
            return 'ggb'
        
        # 3. 基于文件路径的分类
        file_path = metadata.get('file_path', '')
        if '教学大纲' in file_path:
            return 'syllabus'
        elif '习题' in file_path:
            return 'exercise'
        elif '教案' in file_path:
            return 'lesson_plan'
        elif '课例' in file_path:
            return 'lesson_case'
        elif '课件' in file_path:
            return 'courseware'
        
        # 3. 基于主题的动态分类
        title = metadata.get('title', '')
        detected_themes = self.theme_matcher.dynamic_theme_detection(content, title)
        if detected_themes:
            primary_theme = detected_themes[0]['theme']
            # 根据主题调整分类
            if '函数' in primary_theme:
                # 函数相关资源更可能是理论资源
                if '习题' not in content and '题目' not in content:
                    return 'theory_resources'
        
        # 4. 基于查询的动态分类
        if '教案' in query:
            if '教案' in content or '教学' in content:
                return 'lesson_plan_patterns'
        elif '教学大纲' in query:
            if '教学大纲' in content or '教学任务' in content:
                return 'syllabus_resources'
        elif '课例' in query or '教学视频' in query:
            if '课例' in content or '课堂实录' in content or '教学视频' in content:
                return 'lesson_case_resources'
        elif '习题' in query or '题目' in query or '选择题' in query or '填空题' in query or '解答题' in query or '证明题' in query or '练习题' in query:
            if '习题' in content or '题目' in content or '选择题' in content or '填空题' in content or '解答题' in content or '证明题' in content or '练习' in content:
                return 'exercise_resources'
        elif '课件' in query:
            if '课件' in content or 'PPT' in content:
                return 'courseware_resources'
        
        return None
    
    def _apply_grade_filter(self, classified: Dict[str, Any], grade_info: Dict[str, Any], query: str = "") -> Dict[str, Any]:
        """
        V33.0: 应用年级过滤
        
        Args:
            classified: 分类后的资源
            grade_info: 年级信息
            query: 查询文本
        
        Returns:
            过滤后的资源
        """
        target_grade = grade_info.get('grade', '')
        if not target_grade:
            return classified
        
        grade_keywords = {
            '高一上学期': ['必修一', '必修第一册', '高一上', '第一章', '第二章', '第三章', '第四章', '第五章'],
            '高一下学期': ['必修二', '必修第二册', '高一下', '第六章', '第七章', '第八章', '第九章', '第十章'],
            '高二上学期': ['选择性必修一', '高二上', '必修一', '必修二'],  # 增加必修一和必修二
            '高二下学期': ['选择性必修二', '高二下', '必修一', '必修二'],  # 增加必修一和必修二
            '高三': ['选择性必修三', '高三', '高考', '必修一', '必修二', '选择性必修一', '选择性必修二'],  # V52.0改进：高三可以匹配所有年级
            '高一': ['必修一', '必修二', '必修第一册', '必修第二册', '高一'],
            '高二': ['选择性必修一', '选择性必修二', '选择性必修三', '高二', '必修一', '必修二'],  # 增加必修一和必修二
        }
        
        keywords = grade_keywords.get(target_grade, [])
        if not keywords:
            return classified
        
        # V53.1改进：使用动态生成的主题关键词，而不是硬编码
        # 这样当资源库扩展时，系统也能自动适应
        
        # V94.0改进：优化年级过滤逻辑
        # - 高一高二：年级词不重要，重点在于知识点匹配，完全禁用年级过滤
        # - 高三：年级比较重要，因为是复习巩固，但也可以匹配所有年级
        if target_grade in ['高一', '高二']:
            print(f"   🎓 V94.0高一高二查询: 禁用年级过滤，重点在知识点匹配")
            return classified
        elif target_grade == '高三':
            print(f"   🎓 V52.0高三查询: 禁用年级过滤，允许所有年级资源（复习性质）")
            return classified
        
        # 增强的年级匹配逻辑
        print(f"   🎓 应用年级过滤: 目标年级='{target_grade}', 关键词={keywords}")
        
        for category in classified:
            if isinstance(classified[category], list):
                filtered = []
                for resource in classified[category]:
                    # 获取资源信息
                    source_file = resource.get('source', '')
                    title = resource.get('title', '')
                    
                    # 获取知识点标签（可能在metadata中或直接在resource中）
                    metadata = resource.get('metadata', {})
                    knowledge_tags = metadata.get('知识点标签', '')
                    content = resource.get('content', '')
                    
                    # 检查是否包含年级关键词
                    match_found = False
                    for keyword in keywords:
                        if keyword in source_file or keyword in title or keyword in knowledge_tags or keyword in content:
                            match_found = True
                            print(f"   ✅ 年级关键词匹配: '{keyword}' 在 '{title}' 中")
                            break
                    
                    # V53.1改进：如果是跨年级主题，允许更宽松的年级匹配
                    if not match_found:
                        is_cross_grade_topic = False
                        for keyword in self.all_theme_keywords:
                            if keyword in knowledge_tags or keyword in title or keyword in content or keyword in source_file:
                                is_cross_grade_topic = True
                                break
                        
                        if is_cross_grade_topic:
                            # 对于跨年级主题，允许跨年级匹配
                            # 例如：高二的三角函数查询可以匹配高一的三角函数资源
                            match_found = True
                            print(f"   🎓 跨年级主题宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    # 特殊处理2：如果是习题资源，允许更宽松的年级匹配
                    if not match_found:
                        resource_type = metadata.get('resource_type', '')
                        if resource_type == 'exercise':
                            # 对于习题资源，只要主题相关，就允许跨年级匹配
                            match_found = True
                            print(f"   🎓 习题资源宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    # 特殊处理3：如果查询包含"应用"关键词，允许更宽松的年级匹配
                    if not match_found:
                        if '应用' in query or '应用题' in query:
                            # 对于应用题查询，只要主题相关，就允许跨年级匹配
                            match_found = True
                            print(f"   🎓 应用题查询宽松匹配: '{title}' (目标年级: {target_grade})")
                    
                    if match_found:
                        filtered.append(resource)
                    else:
                        print(f"   🎓 年级过滤移除: '{title}' (目标年级: {target_grade})")
                
                classified[category] = filtered
                print(f"   📊 {category} 过滤后剩余 {len(filtered)} 条资源")
        
        return classified
    
    def _apply_topic_exclusion(self, classified: Dict[str, Any], clarified_topic: Dict[str, Any]) -> Dict[str, Any]:
        """
        V33.0: 应用主题排除过滤
        
        Args:
            classified: 分类后的资源
            clarified_topic: 澄清后的主题信息
        
        Returns:
            过滤后的资源
        """
        exclude_keywords = clarified_topic.get('exclude_keywords_matched', [])
        if not exclude_keywords:
            return classified
        
        for category in classified:
            if isinstance(classified[category], list):
                filtered = []
                for resource in classified[category]:
                    content = resource.get('content', '')
                    title = resource.get('title', '')
                    knowledge_tags = resource.get('metadata', {}).get('知识点标签', '')
                    
                    should_exclude = False
                    for keyword in exclude_keywords:
                        if keyword in content or keyword in title or keyword in knowledge_tags:
                            should_exclude = True
                            print(f"   🔍 V33.0主题排除移除: '{title}' (排除关键词: {keyword})")
                            break
                    
                    if not should_exclude:
                        filtered.append(resource)
                
                classified[category] = filtered
        
        return classified
    
    def _apply_quantity_limit(self, classified: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """
        V33.0: 应用数量限制
        
        Args:
            classified: 分类后的资源
            limit: 数量限制
        
        Returns:
            限制后的资源
        """
        total_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
        
        if total_count <= limit:
            print(f"   📊 V33.0数量限制: 资源不足（{total_count}个），返回所有资源")
            # V96.0改进：添加资源不足的提示
            # 向classified中添加资源不足的提示信息
            if 'message' not in classified:
                classified['message'] = []
            classified['message'].append(f"资源不足，已返回所有可用资源（共{total_count}个）")
            return classified
        
        all_resources = []
        for category in classified:
            if isinstance(classified[category], list):
                for resource in classified[category]:
                    resource['_category'] = category
                    all_resources.append(resource)
        
        all_resources.sort(key=lambda x: -x.get('relevance', 0))
        
        limited_resources = all_resources[:limit]
        
        new_classified = {key: [] for key in classified.keys()}
        for resource in limited_resources:
            category = resource.pop('_category', 'general_resources')
            if category in new_classified:
                new_classified[category].append(resource)
        
        print(f"   📊 V33.0数量限制: 原始{total_count}个 -> 限制后{len(limited_resources)}个")
        
        return new_classified
    
    def _get_metadata(self, results: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        安全地获取元数据
        
        Args:
            results: 查询结果
            index: 索引
        
        Returns:
            元数据字典
        """
        if results.get("metadatas") and results["metadatas"][0]:
            if index < len(results["metadatas"][0]):
                return results["metadatas"][0][index]
        return {}
    
    def _get_distance(self, results: Dict[str, Any], index: int) -> float:
        """
        安全地获取距离
        
        Args:
            results: 查询结果
            index: 索引
        
        Returns:
            距离值
        """
        if results.get("distances") and results["distances"][0]:
            if index < len(results["distances"][0]):
                return results["distances"][0][index]
        return 0.0
    
    def _create_resource(self, doc: str, metadata: Dict[str, Any], distance: float, resource_type: str, core_theme: str = "", resource_types: List[str] = None, query: str = "", question_type: str = "") -> Dict[str, Any]:
        """
        创建资源对象（带主题匹配）- V2改进版
        使用置信度评估和主题组合合理性检查
        
        Args:
            doc: 文档内容
            metadata: 元数据
            distance: 距离
            resource_type: 资源类型
            core_theme: 核心主题
            resource_types: 用户明确指定的资源类型列表
            query: 用户查询（V32.0新增）
        
        Returns:
            资源字典
        """
        # 基本资源信息 - 保留原始相似度作为基础分！
        # ChromaDB返回的是欧几里得距离，范围在[0, ∞)之间
        # 正确的相关性计算应该是1 / (1 + distance)，这样相关性得分会在[0, 1]之间
        base_relevance = 1 / (1 + distance)
        # 提取习题相关信息
        difficulty = metadata.get('难度', '') or metadata.get('difficulty', '') or metadata.get('难度（1-5）', '')
        question_type = metadata.get('题目类型', '')
        knowledge_points = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        
        resource = {
            "title": metadata.get('title', '未知'),
            "content": doc,
            "source": metadata.get('source_file', ''),
            "relevance": base_relevance,
            "metadata": metadata,
            "base_relevance": base_relevance,
            "theme_match": False,
            "type_match": False,
            "matched_theme_count": 0,
            "theme_boost": 0.0,
            "conflict_theme": False,
            "matched_themes": [],  # 记录匹配的所有主题
            "is_comprehensive": False,  # 是否为综合性资源（匹配多个主题）
            "难度": difficulty,  # 习题难度
            "题目类型": question_type,  # 习题题型
            "知识点": knowledge_points  # 知识点
        }
        
        # 改进：检查元数据中是否已有主题匹配信息（来自多主题检索）
        multi_theme_info = metadata.get("_matched_themes", [])
        
        # 暂时存储多主题检索的信息，供调试使用
        resource["multi_theme_retrieval_info"] = {
            "matched_themes": metadata.get("_matched_themes", []),
            "matched_theme_count": metadata.get("_matched_theme_count", 0),
            "theme_distances": metadata.get("_theme_distances", {})
        }
        
        # 重要修复：多主题检索时，优先使用多主题检索的结果
        # 只有在没有多主题检索结果时，才使用 ThemeMatcherV90 进行核心主题识别
        if multi_theme_info and len(multi_theme_info) > 0:
            # V30.1改进：首先验证多主题检索的结果是否包含查询主题
            # 如果不包含查询主题，说明主题匹配有误，应该使用查询主题
            query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
            
            # 检查多主题检索的结果是否包含查询主题
            has_query_theme_in_multi = any(qt in multi_theme_info for qt in query_themes)
            print(f"   🔍 V30.1调试: query_themes={query_themes}, multi_theme_info={multi_theme_info}, has_query_theme_in_multi={has_query_theme_in_multi}")
            
            if not has_query_theme_in_multi:
                # V30.1修复：多主题检索结果不包含查询主题，这是一个严重的主题误标问题
                # 强制使用查询主题作为匹配主题
                print(f"   ⚠️ V30.1主题误标修复: 多主题检索结果{multi_theme_info}不包含查询主题{query_themes}，强制使用查询主题")
                matched_themes = query_themes
                matched_theme_count = len(matched_themes)
                core_theme_match = query_themes[0] if query_themes else None
                relevance_score = base_relevance
                theme_distances = {}  # 初始化 theme_distances 变量
                
                # 跳过排除词检查，直接使用查询主题
                valid_themes = matched_themes
            else:
                # 使用多主题检索的结果
                matched_themes = multi_theme_info
                matched_theme_count = len(matched_themes)
                
                # 计算平均距离，作为相关性的参考
                theme_distances = metadata.get("_theme_distances", {})
                if theme_distances:
                    avg_distance = sum(theme_distances.values()) / len(theme_distances)
                    relevance_score = 1 / (1 + avg_distance)  # 统一使用与单主题检索相同的计算方式
                else:
                    relevance_score = 0.8  # 默认值
                
                # 确定核心主题：选择距离最小的主题作为核心主题
                if theme_distances:
                    core_theme_match = min(theme_distances, key=theme_distances.get)
                else:
                    core_theme_match = matched_themes[0] if matched_themes else None
                
                # 关键修复：使用V90主题匹配器进行排除词检查
                from .theme_matcher_v90 import get_theme_matcher_v90
                theme_matcher_v90 = get_theme_matcher_v90()
                
                # V16.1改进：对于多主题检索，放宽排除词检查
                # 只有当资源包含其他非查询主题的关键词时，才排除
                # 例如：查询"指数函数和对数函数"，资源包含"三角函数"应该被排除
                # 但资源同时包含"指数"和"对数"不应该被排除
                valid_themes = []
                for theme in matched_themes:
                    # 获取该主题的排除词
                    exclusion_words = theme_matcher_v90.theme_exclusion_words.get(theme, [])
                    
                    # 过滤掉与当前查询主题相关的排除词
                    # 例如：查询"指数函数和对数函数"，"对数"不应该作为"指数函数"的排除词
                    filtered_exclusion_words = []
                    # 使用core_themes（查询的主题）而不是matched_themes（匹配的主题）来过滤排除词
                    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                    for word in exclusion_words:
                        # 检查排除词是否是其他查询主题的关键词
                        is_other_theme_keyword = False
                        for other_theme in query_themes:
                            if other_theme != theme and word in other_theme:
                                is_other_theme_keyword = True
                                break
                        if not is_other_theme_keyword:
                            filtered_exclusion_words.append(word)
                    
                    print(f"    🔍 主题 '{theme}' 的排除词: {exclusion_words}")
                    print(f"    🔍 查询主题: {query_themes}")
                    print(f"    🔍 过滤后的排除词: {filtered_exclusion_words}")
                    
                    # V16.5改进：放宽排除词检查，只过滤掉明确的知识点冲突
                    # 例如：如果习题是关于指数函数的，即使包含"二次"关键词，只要不是主要知识点，也应该允许通过
                    full_text = f"{metadata.get('title', '')} {doc}".lower()
                    has_exclusion_word = False
                    
                    # 定义明确的知识点排除词（只过滤这些）
                    explicit_exclusion_words = ["幂函数", "三角函数", "二次函数", "一次函数", "分段函数", "三角", "sin", "cos", "tan"]
                    
                    for word in filtered_exclusion_words:
                        # 只检查明确的知识点排除词，不检查通用词汇
                        if word in explicit_exclusion_words:
                            if word.lower() in full_text:
                                has_exclusion_word = True
                                print(f"    ⚠️ 多主题检索：'{metadata.get('title', '未知')}' 与主题 '{theme}' 不匹配（包含排除词 '{word}'）")
                                break
                    
                    if not has_exclusion_word:
                        valid_themes.append(theme)
                    else:
                        print(f"    ⚠️ 多主题检索：'{metadata.get('title', '未知')}' 与主题 '{theme}' 不匹配（包含排除词）")
            
            # V16.2改进：如果没有有效的主题，使用原始匹配主题作为备选
            # 确保即使排除词检查失败，也能保留至少一个主题
            if not valid_themes and matched_themes:
                valid_themes = matched_themes[:1]  # 保留第一个匹配的主题
                print(f"    ⚠️ 多主题检索：无有效主题，使用备选主题: {valid_themes}")
            
            # 更新匹配的主题列表
            matched_themes = valid_themes
            matched_theme_count = len(matched_themes)
            
            # 计算基础相关性（多主题检索中使用relevance_score）
            base_relevance = relevance_score
            
            # 如果没有有效的主题，标记为不匹配
            if matched_theme_count == 0:
                core_theme_match = None
                related_themes = []
                mentioned_themes = []
                is_core_match = False
                match_level = "none"
                domain = "未知"
                explanation = "多主题检索结果经排除词检查后无有效匹配"
                should_show = False
                relevance_score = 0.0
                overall_score = 0.0
                resource_quality = 0.0
                content_completeness = 0.0
                teaching_value = 0.0
                comprehensiveness = 0.0
                concept_hierarchy_factor = 0.5
            else:
                # 重新确定核心主题
                if theme_distances:
                    # 只考虑有效的主题
                    valid_theme_distances = {k: v for k, v in theme_distances.items() if k in valid_themes}
                    if valid_theme_distances:
                        core_theme_match = min(valid_theme_distances, key=valid_theme_distances.get)
                    else:
                        core_theme_match = valid_themes[0]
                else:
                    core_theme_match = valid_themes[0]
                
                related_themes = [theme for theme in valid_themes if theme != core_theme_match]
                mentioned_themes = []
                is_core_match = True
                match_level = "core"
                domain = "多主题"
                explanation = f"匹配到{matched_theme_count}个主题: {', '.join(valid_themes)}"
                should_show = True
                overall_score = relevance_score
                resource_quality = 0.5
                content_completeness = 0.3
                teaching_value = 0.15
                comprehensiveness = 0.2
                concept_hierarchy_factor = 0.5
        elif core_theme:
            # 没有多主题检索结果，使用V9.0主题匹配器进行核心主题识别
            # 支持多个核心主题（用逗号分隔）
            core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
            
            # 检查是否是习题资源
            is_exercise = resource_type == "exercise"
            
            if is_exercise:
                # 对于习题资源，使用特殊的相关性计算方法
                print(f"   📝 检测到习题资源，使用习题相关性计算方法")
                
                # 提取习题相关信息
                question_content = metadata.get("题干", "") or doc
                question_file = metadata.get("题目文件名", "")
                source_file = metadata.get("source_file", "")
                title = metadata.get("title", "")
                
                # 计算习题与主题的相关性
                relevance_score = 0.0
                matched_themes = []
                core_theme_match = None
                related_themes = []
                mentioned_themes = []
                is_core_match = False
                match_level = "none"
                domain = "习题"
                explanation = "习题相关性评估"
                should_show = False
                overall_score = 0.0
                resource_quality = 0.5
                content_completeness = 0.3
                teaching_value = 0.15
                comprehensiveness = 0.2
                concept_hierarchy_factor = 0.5
                
                # 检查知识点一致性
                is_consistent = self._check_knowledge_point_consistency(metadata, core_theme, question_content, query, relevance)
                
                # V20.1改进：严格检查知识点标签
                # 如果知识点标签明确包含非查询主题，则直接过滤（相关性设为0）
                # V30.7修复：同时检查"知识点"和"知识点标签"两个字段名
                knowledge_tags = metadata.get("知识点", "") or metadata.get("知识点标签", "")
                strict_match = True
                
                # V21.0改进：处理缺少知识点标签的情况
                # 如果知识点标签为空，尝试从题目内容中提取关键词
                if not knowledge_tags and question_content:
                    # 从题目内容中提取可能的知识点
                    all_math_themes = ["二次函数", "幂函数", "三角函数", "指数函数", "对数函数", "函数的零点", "一次函数", "集合", "不等式", "三角恒等变换"]
                    extracted_themes = [t for t in all_math_themes if t in question_content]
                    if extracted_themes:
                        knowledge_tags = ";".join(extracted_themes)
                        print(f"   🔍 V21.0：从题目内容提取知识点标签: '{knowledge_tags}'")
                        # V22.2改进：更新metadata，以便后续检查使用
                        metadata["知识点"] = knowledge_tags
                
                if knowledge_tags and core_themes:
                    # V30.6修复：对于"函数的概念"主题，需要更严格的检查
                    # 检查是否是严格过滤主题
                    strict_filter_themes = ["函数概念", "函数的概念"]
                    is_strict_filter_theme = any(st in core_theme for st in strict_filter_themes)
                    
                    # 检查是否是通用主题（如"函数"）
                    generic_themes = ["函数", "数学", "教学", "函数的应用", "高中数学", "数学教学"]
                    is_generic_theme = any(gt in core_theme for gt in generic_themes)
                    
                    if is_strict_filter_theme:
                        # 检查是否是GGB资源，如果是且知识点标签为unknown，允许通过
                        resource_type = metadata.get('resource_type', '')
                        if resource_type == 'ggb' and (not knowledge_tags or knowledge_tags == 'unknown'):
                            print(f"   ✅ V61.0GGB资源特殊处理: GGB资源知识点标签为unknown，允许通过筛选")
                            strict_match = True
                        else:
                            # 对于严格过滤主题，检查知识点标签是否包含相关关键词
                            concept_keywords = ["函数概念", "函数的定义", "什么是函数", "函数的意义", "函数表示", "函数表示法", "映射", "对应关系", "自变量", "因变量"]
                            has_concept_keyword = any(keyword in knowledge_tags for keyword in concept_keywords)
                            
                            if not has_concept_keyword:
                                # 知识点标签不包含函数概念相关关键词，严格过滤
                                print(f"   ⚠️ V30.6严格过滤：知识点标签'{knowledge_tags}'不包含函数概念相关关键词，严格过滤")
                                relevance_score = 0.0
                                overall_score = 0.0
                                should_show = False
                                is_core_match = False
                                match_level = "none"
                                explanation = f"知识点标签不包含函数概念相关关键词"
                                strict_match = False
                    elif not is_generic_theme:
                        # 非严格过滤主题且非通用主题，使用原有逻辑
                        # 检查知识点标签是否包含查询主题
                        has_query_theme = any(theme in knowledge_tags for theme in core_themes)
                        # 检查知识点标签是否包含其他数学主题（非查询主题）
                        all_math_themes = ["二次函数", "幂函数", "三角函数", "指数函数", "对数函数", "函数的零点", "一次函数", "集合", "不等式", "三角恒等变换"]
                        other_themes_in_tags = [t for t in all_math_themes if t in knowledge_tags and t not in core_themes]
                        
                        if not has_query_theme and other_themes_in_tags:
                            # 知识点标签包含其他主题，但不包含查询主题，严格过滤
                            print(f"   ⚠️ V20.1严格过滤：知识点标签'{knowledge_tags}'包含非查询主题{other_themes_in_tags}，但不包含查询主题{core_themes}")
                            relevance_score = 0.0
                            overall_score = 0.0
                            should_show = False
                            is_core_match = False
                            match_level = "none"
                            explanation = f"知识点标签与查询主题不符"
                            strict_match = False
                    else:
                        # V53.1改进：通用主题（如"函数"、"概率"、"立体几何"），允许包含任何相关的知识点标签
                        print(f"   ✅ V37.1通用主题处理：查询主题'{core_theme}'是通用主题，允许包含相关知识点标签")
                        # V53.1改进：使用动态生成的主题关键词，而不是硬编码
                        has_related_keyword = any(keyword in knowledge_tags for keyword in self.all_theme_keywords)
                        if has_related_keyword:
                            print(f"   ✅ V37.1通用主题匹配：知识点标签'{knowledge_tags}'包含相关关键词，通过筛选")
                            strict_match = True
                        else:
                            # V39.0改进：如果知识点标签中包含核心主题关键词，也视为匹配
                            core_theme_keywords = self.knowledge_hierarchy.get(core_theme, {}).get('keywords', [])
                            if any(kw in knowledge_tags for kw in core_theme_keywords):
                                print(f"   ✅ V39.0通用主题匹配：知识点标签'{knowledge_tags}'包含核心主题关键词，通过筛选")
                                strict_match = True
                            else:
                                print(f"   ⚠️ V37.1通用主题过滤：知识点标签'{knowledge_tags}'不包含相关关键词，严格过滤")
                                relevance_score = 0.0
                                overall_score = 0.0
                                should_show = False
                                is_core_match = False
                                match_level = "none"
                                explanation = f"知识点标签与查询主题不符"
                                strict_match = False
                
                # V43.0改进：修改判断逻辑，优先考虑is_consistent的结果
                # 如果is_consistent为True，即使strict_match为False，也应该认为匹配成功
                if is_consistent:
                    # 如果知识点一致，使用基础相关性
                    relevance_score = base_relevance
                    overall_score = base_relevance
                    should_show = True
                    is_core_match = True
                    match_level = "core"
                    # 重要修复：如果是多主题检索，保留多主题检索的结果
                    # 否则使用核心主题
                    if not multi_theme_info:
                        matched_themes = core_themes
                        core_theme_match = core_themes[0] if core_themes else None
                    explanation = f"习题知识点与主题一致: {core_theme}"
                elif strict_match:
                    # 如果strict_match为True但is_consistent为False，使用较低的相关性
                    # 非严格过滤主题，如果知识点不一致，使用较低的相关性
                    relevance_score = base_relevance * 0.5
                    overall_score = relevance_score
                    should_show = relevance_score > 0.1
                    match_level = "related"
                    explanation = f"习题知识点与主题部分相关: {core_theme}"
                else:
                    # V30.4修复：对于"函数的概念"等需要严格过滤的主题，如果不一致则直接过滤
                    # 检查是否是严格过滤主题
                    strict_filter_themes = ["函数概念", "函数的概念"]
                    is_strict_filter_theme = any(st in core_theme for st in strict_filter_themes)
                    
                    if is_strict_filter_theme:
                        # 严格过滤主题，如果不一致则直接过滤
                        print(f"   ⚠️ V30.4严格过滤: '{core_theme}'主题需要严格匹配，知识点不一致，直接过滤")
                        relevance_score = 0.0
                        overall_score = 0.0
                        should_show = False
                        is_core_match = False
                        match_level = "none"
                        explanation = f"严格过滤主题'{core_theme}'知识点不匹配"
                    else:
                        # 非严格过滤主题，如果知识点不一致，使用较低的相关性
                        relevance_score = base_relevance * 0.3
                        overall_score = relevance_score
                        should_show = relevance_score > 0.1
                        match_level = "related"
                        explanation = f"习题知识点与主题部分相关: {core_theme}"
                
                # V46.1改进：对于单调性证明题，提升相关性分数（无论is_consistent结果如何）
                if (question_type == '证明题' and '单调性' in core_theme) or ('证明' in query and '单调性' in query):
                    # 提升单调性证明题的相关性分数，确保它们能通过阈值过滤
                    old_relevance = relevance_score
                    relevance_score = max(relevance_score, 0.8)  # 设置最低相关性为0.8，进一步提高
                    overall_score = relevance_score
                    print(f"   🔍 V46.1单调性证明题: 提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
                    is_core_match = True
                    match_level = "core"
                    explanation = f"单调性证明题，提升相关性分数: {core_theme}"
                    should_show = True
                # V46.2改进：对于包含单调性证明内容的习题，也提升相关性分数（无论is_consistent结果如何）
                elif '单调性' in question_content and ('证明' in question_content or '求证' in question_content):
                    old_relevance = relevance_score
                    relevance_score = max(relevance_score, 0.7)  # 设置最低相关性为0.7
                    overall_score = relevance_score
                    print(f"   🔍 V46.2单调性证明题: 基于内容提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
                    is_core_match = True
                    match_level = "core"
                    explanation = f"单调性证明题，基于内容提升相关性分数: {core_theme}"
                    should_show = True
                # V46.3改进：对于知识点标签包含单调性的习题，也提升相关性分数（无论is_consistent结果如何）
                elif '单调性' in knowledge_tags and question_type == '证明题':
                    old_relevance = relevance_score
                    relevance_score = max(relevance_score, 0.6)  # 设置最低相关性为0.6
                    overall_score = relevance_score
                    print(f"   🔍 V46.3单调性证明题: 基于知识点标签提升习题相关性分数 {old_relevance:.4f} -> {relevance_score:.4f}")
                    is_core_match = True
                    match_level = "core"
                    explanation = f"单调性证明题，基于知识点标签提升相关性分数: {core_theme}"
                    should_show = True
                
                # V28.0：年级筛选（V32.0改进：宽泛查询广泛推荐策略）
                # V46.0修复：确保is_vague_query在所有情况下都有定义
                is_vague_query = False
                if should_show and self._current_grade_info:
                    # V32.0：判断是否是宽泛查询（只有年级，没有具体主题或难度要求）
                    is_vague_query = self._is_vague_grade_query(query, self._current_grade_info)
                    
                    if is_vague_query:
                        # V32.0：宽泛查询 - 放宽年级筛选，允许各年级相关内容
                        print(f"   🎓 V32.0宽泛查询模式: 放宽年级筛选，广泛推荐")
                        grade_filter_result = self._apply_flexible_grade_filter(metadata, self._current_grade_info)
                    else:
                        # V32.0：具体查询 - 严格年级筛选
                        grade_filter_result = self._check_grade_match(metadata, self._current_grade_info)
                    
                    if not grade_filter_result['pass']:
                        print(f"   🎓 V32.0年级筛选: {grade_filter_result['reason']}")
                        should_show = False
                        relevance_score = 0.0
                        overall_score = 0.0
                        explanation = f"{explanation} (年级不符: {grade_filter_result['reason']})"
                
                # V28.0：主观意图筛选（V32.0改进：支持宽泛查询灵活匹配）
                if should_show and self._current_subjective_intent:
                    intent_filter_result = self._apply_subjective_intent_filter(metadata, self._current_subjective_intent, is_vague_query)
                    if not intent_filter_result['pass']:
                        print(f"   💭 V32.0主观意图筛选: {intent_filter_result['reason']}")
                        should_show = False
                        relevance_score = 0.0
                        overall_score = 0.0
                        explanation = f"{explanation} (主观意图不符: {intent_filter_result['reason']})"
                    else:
                        # 如果通过主观意图筛选，调整相关性得分
                        if intent_filter_result.get('score_adjustment'):
                            old_relevance = relevance_score
                            relevance_score *= intent_filter_result['score_adjustment']
                            overall_score *= intent_filter_result['score_adjustment']
                            print(f"   💭 V32.0主观意图调整: 相关性 {old_relevance:.3f} -> {relevance_score:.3f} (乘以 {intent_filter_result['score_adjustment']})")
            else:
                # 非习题资源，使用V9.0主题匹配器进行核心主题识别
                # V54.0改进：根据资源类型使用不同的评估方法
                from .theme_matcher_v90 import get_theme_matcher_v90
                theme_matcher_v90 = get_theme_matcher_v90()
                
                # V54.0改进：教案资源使用精准匹配，其他资源使用简化匹配
                if resource_type == 'lesson_plan':
                    # 教案资源使用精准匹配计算
                    precise_match_result = theme_matcher_v90.calculate_precise_match(
                        query=core_theme,
                        lesson_title=metadata.get("title", ""),
                        lesson_content=doc,
                        metadata=metadata
                    )
                    
                    # 提取匹配结果（V9.0格式）
                    relevance_score = precise_match_result["relevance_score"]
                    matched_themes = precise_match_result["matched_themes"]
                    core_theme_match = precise_match_result["core_theme"]
                    related_themes = precise_match_result["related_themes"]
                    mentioned_themes = precise_match_result["mentioned_themes"]
                    is_core_match = precise_match_result["is_core_match"]
                    match_level = precise_match_result["match_level"]
                    domain = precise_match_result["domain"]
                    explanation = precise_match_result["explanation"]
                    should_show = precise_match_result["should_show"]
                    
                    # V10.0：提取多维度评估指标
                    overall_score = precise_match_result.get("overall_score", relevance_score)
                    resource_quality = precise_match_result.get("resource_quality", None)
                    content_completeness = precise_match_result.get("content_completeness", None)
                    teaching_value = precise_match_result.get("teaching_value", None)
                    comprehensiveness = precise_match_result.get("comprehensiveness", None)
                    
                    # V11.0：提取概念层级因子
                    concept_hierarchy_factor = precise_match_result.get("concept_hierarchy_factor", 0.5)
                else:
                    # V54.0改进：其他资源类型（课件、教学大纲、课例视频、GGB等）使用简化匹配
                    # V61.0改进：使用动态配置获取主题关键词，避免硬编码
                    
                    # 提取查询主题
                    query_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
                    
                    # 检查内容是否包含查询主题
                    matched_themes = []
                    for theme in query_themes:
                        if theme in doc or theme in metadata.get("title", ""):
                            matched_themes.append(theme)
                    
                    # V61.0改进：使用动态配置获取主题关键词
                    theme_keywords = []
                    for theme in query_themes:
                        theme_keywords.extend(self.config_loader.get_theme_keywords(theme))
                    
                    # 检查内容是否包含主题关键词
                    matched_keywords = []
                    for keyword in theme_keywords:
                        if keyword in doc or keyword in metadata.get("title", ""):
                            matched_keywords.append(keyword)
                    
                    # 对于课件资源，使用更灵活的匹配逻辑
                    # V90.0修复：降低课件资源的相关性阈值，因为课件资源的文档内容质量较差
                    if resource_type == 'courseware':
                        # V90.2调试：添加调试信息
                        print(f"   🔍 V90.2课件资源调试 - base_relevance: {base_relevance:.4f}, matched_keywords: {matched_keywords}, theme_keywords: {theme_keywords}")
                        
                        # 如果匹配到主题关键词，提高相关性
                        if matched_keywords:
                            is_core_match = True
                            match_level = "core"
                            keyword_match_score = min(len(matched_keywords) / max(len(theme_keywords), 1), 1.0)
                            relevance_score = base_relevance * (0.7 + 0.3 * keyword_match_score)
                            core_theme_match = query_themes[0] if query_themes else None
                            related_themes = query_themes[1:] if len(query_themes) > 1 else []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = f"匹配到主题关键词: {', '.join(matched_keywords[:5])}"
                            should_show = keyword_match_score >= 0.2  # V90.0修复：降低阈值从0.3到0.2
                            print(f"   🔍 V90.2课件资源 - 匹配到关键词: {keyword_match_score:.4f} >= 0.2, should_show: {should_show}")
                        else:
                            is_core_match = False
                            match_level = "related"
                            relevance_score = base_relevance * 0.5
                            core_theme_match = None
                            related_themes = []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = "基于向量相似度匹配"
                            should_show = base_relevance > 0.10  # V90.0修复：降低阈值从0.30到0.10
                            print(f"   🔍 V90.2课件资源 - 基础相关性: {base_relevance:.4f} > 0.10, should_show: {should_show}")
                    # 对于习题资源，使用更灵活的匹配逻辑
                    elif resource_type == 'exercise':
                        # V61.0改进：使用动态配置获取主题关键词
                        if matched_keywords:
                            is_core_match = True
                            match_level = "core"
                            keyword_match_score = min(len(matched_keywords) / max(len(theme_keywords), 1), 1.0)
                            relevance_score = base_relevance * (0.7 + 0.3 * keyword_match_score)
                            core_theme_match = query_themes[0] if query_themes else None
                            related_themes = query_themes[1:] if len(query_themes) > 1 else []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = f"匹配到主题关键词: {', '.join(matched_keywords[:5])}"
                            should_show = keyword_match_score >= 0.3
                        else:
                            is_core_match = False
                            match_level = "related"
                            relevance_score = base_relevance * 0.5
                            core_theme_match = None
                            related_themes = []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = "基于向量相似度匹配"
                            should_show = base_relevance > 0.30
                    else:
                        # 其他资源类型使用原有逻辑
                        # 计算相关性
                        if matched_themes:
                            is_core_match = True
                            match_level = "core"
                            relevance_score = base_relevance
                            core_theme_match = matched_themes[0]
                            related_themes = matched_themes[1:] if len(matched_themes) > 1 else []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = f"匹配到主题: {', '.join(matched_themes)}"
                            should_show = True
                        else:
                            # 没有明确匹配，使用基础相关性
                            is_core_match = False
                            match_level = "related"
                            relevance_score = base_relevance * 0.5
                            core_theme_match = None
                            related_themes = []
                            mentioned_themes = []
                            domain = resource_type
                            explanation = "基于向量相似度匹配"
                            should_show = base_relevance > 0.30
                    
                    # V54.0改进：为非教案资源设置合理的多维度评估指标
                    overall_score = relevance_score
                    resource_quality = 0.5
                    content_completeness = 0.5
                    teaching_value = 0.5
                    comprehensiveness = 0.5
                    concept_hierarchy_factor = 0.5
        else:
            # 没有核心主题，使用默认值
            matched_themes = []
            matched_theme_count = 0
            core_theme_match = None
            related_themes = []
            mentioned_themes = []
            is_core_match = False
            match_level = "none"
            domain = "未知"
            explanation = "未匹配到主题"
            
            # 检查是否有习题类型要求
            query_features = getattr(self, '_current_query_features', {})
            has_exercise_type_requirement = query_features.get('required_exercise_type') is not None
            has_difficulty_requirement = query_features.get('required_difficulty') is not None
            
            # V53.13改进：对于非习题资源（如课件、教案），只要基础相关性足够高就显示
            # 不再要求必须有习题类型或难度要求
            # V90.0修复：对于课件资源，使用更低的阈值，因为课件资源的文档内容质量较差
            min_relevance_threshold = 0.10 if resource_type == 'courseware' else 0.30  # 课件资源使用0.10，其他资源使用0.30
            print(f"   🔍 V53.13调试 - base_relevance: {base_relevance:.4f}, threshold: {min_relevance_threshold}, resource_type: {resource_type}")
            if base_relevance >= min_relevance_threshold:
                should_show = True
                # 使用基础相关性作为得分
                relevance_score = base_relevance
                overall_score = base_relevance
                resource_quality = 0.5
                content_completeness = 0.3
                teaching_value = 0.15
                comprehensiveness = 0.2
                concept_hierarchy_factor = 0.5
            else:
                should_show = False
                relevance_score = 0.0
                overall_score = 0.0
                resource_quality = 0.0
                content_completeness = 0.0
                teaching_value = 0.0
                comprehensiveness = 0.0
                concept_hierarchy_factor = 0.5
        
        # 确定匹配的主题
        matched_theme_count = len(matched_themes)
        
        # 更新资源中的主题匹配信息
        resource["matched_themes"] = matched_themes
        resource["matched_theme_count"] = matched_theme_count
        resource["core_theme"] = core_theme_match
        resource["related_themes"] = related_themes
        resource["mentioned_themes"] = mentioned_themes
        resource["is_core_match"] = is_core_match
        resource["match_level"] = match_level
        resource["domain"] = domain  # 存储领域信息
        resource["match_explanation"] = explanation
        resource["should_show"] = should_show
        
        # V10.0：存储多维度评估指标（V11.2：确保总是存储，即使没有值也存储0）
        resource["overall_score"] = overall_score
        resource["resource_quality"] = resource_quality if resource_quality is not None else 0.0
        resource["content_completeness"] = content_completeness if content_completeness is not None else 0.0
        resource["teaching_value"] = teaching_value if teaching_value is not None else 0.0
        resource["comprehensiveness"] = comprehensiveness if comprehensiveness is not None else 0.0
        
        # V11.0：存储概念层级因子
        resource["concept_hierarchy_factor"] = concept_hierarchy_factor
        
        # 使用V9.0的真实相关性分数
        avg_theme_score = relevance_score
        
        # 融合计算（V9.0使用主题匹配度作为主要依据）
        final_relevance = relevance_score
        
        # V54.0改进：对于教案资源，使用overall_score判断should_show
        # V92.0改进：根据不同资源类型调整相关性阈值，提高召回率
        # V61.0改进：提高教案资源的阈值，确保相关性
        # V90.2修复：对于课件资源，使用更低的阈值
        if resource_type == 'lesson_plan' and overall_score > 0:
            # V92.0改进：降低教案资源的阈值，提高召回率
            min_overall_threshold = 0.20  # 从0.30降低到0.20
            if overall_score >= min_overall_threshold:
                should_show = True
                final_relevance = max(final_relevance, overall_score)
            else:
                should_show = False
        elif resource_type == 'courseware':
            # V92.0改进：对于课件资源，使用更低的阈值，因为课件资源的文档内容质量较差
            min_relevance_threshold = 0.10  # 保持0.10
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        elif resource_type == 'exercise':
            # V92.0改进：对于习题资源，使用适中的阈值
            min_relevance_threshold = 0.25  # 从0.30降低到0.25
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        elif resource_type == 'ggb':
            # V92.0改进：对于GGB资源，使用更低的阈值
            min_relevance_threshold = 0.15
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        elif resource_type == 'lesson_case':
            # V92.0改进：对于课例资源，使用更低的阈值
            min_relevance_threshold = 0.20
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        elif resource_type == 'syllabus':
            # V92.0改进：对于教学大纲资源，使用更低的阈值
            min_relevance_threshold = 0.20
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        else:
            # 其他资源类型使用默认阈值
            min_relevance_threshold = 0.30
            if final_relevance < min_relevance_threshold and not is_core_match:
                final_relevance = 0.0
                should_show = False
        
        print(f"   🔍 V92.0最终相关性检查 - resource_type: {resource_type}, final_relevance: {final_relevance:.4f}, is_core_match: {is_core_match}, should_show: {should_show}")
        
        # 记录调试信息
        resource["theme_match"] = matched_theme_count > 0
        resource["theme_boost"] = avg_theme_score
        resource["debug_info"] = {
            "base_relevance": base_relevance,
            "avg_theme_score": avg_theme_score,
            "matched_themes": matched_themes,
            "core_theme": core_theme_match,
            "related_themes": related_themes,
            "mentioned_themes": mentioned_themes,
            "is_core_match": is_core_match,
            "match_level": match_level,
            "domain": domain,
            "explanation": explanation,
            "should_show": should_show,
            "formula": f"V9.0统一匹配: {final_relevance:.2f}"
        }
        
        # 确保最终得分在合理范围内
        final_relevance = max(0.0, min(1.0, final_relevance))
        resource["relevance"] = final_relevance
        resource["should_show"] = should_show
        
        # 资源类型优先级加分：当用户明确指定资源类型时，匹配的类型获得额外加分
        if resource_types and not any(rt in ["资料", "资源"] for rt in resource_types):
            from ..config.resource_type_config import get_db_type
            
            # 检查当前资源类型是否匹配用户指定的类型
            type_matched = False
            for user_type in resource_types:
                mapped_db_type = get_db_type(user_type)
                if mapped_db_type and resource_type == mapped_db_type:
                    type_matched = True
                    break
                elif not mapped_db_type and user_type.lower() in resource_type.lower():
                    type_matched = True
                    break
            
            if type_matched:
                # 用户指定类型的资源获得额外加分
                type_boost = 0.05  # 降低类型匹配加分，避免所有资源都显示100%
                final_relevance += type_boost
                final_relevance = min(1.0, final_relevance)  # 确保不超过1.0
                resource["relevance"] = final_relevance
                resource["type_match"] = True
                resource["type_boost"] = type_boost
        
        # 根据资源类型进行特殊处理
        if resource_type == 'exercise':
            # 习题资源特殊处理
            self._process_exercise_resource(resource, metadata)
        elif resource_type == 'ggb':
            # GGB资源特殊处理
            self._process_ggb_resource(resource, metadata)
        elif resource_type == 'syllabus':
            # 教学大纲特殊处理
            self._process_syllabus_resource(resource, metadata)
        elif resource_type == 'lesson_plan':
            # 教案资源特殊处理
            self._process_lesson_plan_resource(resource, metadata)
        elif resource_type == 'courseware':
            # 课件资源特殊处理
            self._process_courseware_resource(resource, metadata)
        elif resource_type == 'lesson_case':
            # 课例资源特殊处理
            self._process_lesson_case_resource(resource, metadata)
        
        # V13.0：质量控制机制
        # 1. 资源质量过滤：如果资源质量过低，降低相关性
        resource_quality = resource.get('resource_quality', 0)
        if resource_quality < 0.3:
            resource["relevance"] *= 0.8  # 质量过低，降低相关性
        
        # 2. 内容完整性过滤：如果内容完整性过低，降低相关性
        content_completeness = resource.get('content_completeness', 0)
        if content_completeness < 0.2:
            resource["relevance"] *= 0.7  # 内容不完整，降低相关性
        
        # 3. 教学价值过滤：如果教学价值过低，降低相关性
        teaching_value = resource.get('teaching_value', 0)
        if teaching_value < 0.1:
            resource["relevance"] *= 0.6  # 教学价值低，降低相关性
        
        # 4. 确保相关性不为负
        resource["relevance"] = max(0.0, resource["relevance"])
        
        # V90.2调试：添加调试信息
        print(f"   🔍 V90.2质量控制 - resource_type: {resource_type}, should_show: {should_show}, relevance: {resource['relevance']:.4f}")
        
        # 5. 综合得分重新计算
        resource["overall_score"] = self._calculate_overall_score(resource, is_core_match)
        
        # V90.2调试：添加调试信息
        print(f"   🔍 V90.2返回资源 - should_show: {should_show}, resource['should_show']: {resource.get('should_show', 'not set')}")
        
        return resource
    
    def _calculate_overall_score(self, resource: Dict[str, Any], is_core_match: bool) -> float:
        """
        计算资源的综合得分
        
        Args:
            resource: 资源对象
            is_core_match: 是否是核心主题匹配
        
        Returns:
            综合得分
        """
        relevance = resource.get('relevance', 0.0)
        resource_quality = resource.get('resource_quality', 0.0)
        content_completeness = resource.get('content_completeness', 0.0)
        teaching_value = resource.get('teaching_value', 0.0)
        comprehensiveness = resource.get('comprehensiveness', 0.0)
        concept_hierarchy_factor = resource.get('concept_hierarchy_factor', 0.5)
        
        # 综合得分计算公式
        # 相关性占主要权重，其他指标作为辅助
        overall_score = (
            relevance * 0.5 +
            resource_quality * 0.15 +
            content_completeness * 0.15 +
            teaching_value * 0.1 +
            comprehensiveness * 0.1
        )
        
        # 如果是核心主题匹配，给予额外加分
        if is_core_match:
            overall_score *= 1.1
        
        # 确保得分在0-1之间
        overall_score = max(0.0, min(1.0, overall_score))
        
        return overall_score
    
    def _process_exercise_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理习题资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        # 获取题目文件名
        filename = metadata.get('题目文件名', '')
        source_file = metadata.get('source_file', '')
        question = metadata.get('题干', '')
        answer = metadata.get('解析', '')
        difficulty = metadata.get('难度（1-5）', '') or metadata.get('难度', '')
        knowledge_tags = metadata.get('知识点', '') or metadata.get('知识点标签', '')
        usage_scene = metadata.get('适用场景', '')
        question_type = metadata.get('题目类型', '')
        
        if filename:
            # 有文件名，说明是图片题目
            resource['title'] = f"习题（图片）: {filename}"
            resource['content'] = f"题目类型：{question_type}\n题目描述：{question}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}\n解析：{answer}"
            resource['is_image_exercise'] = True
            resource['filename'] = filename
            resource['source'] = source_file
        else:
            # 文字题目，显示完整题目
            resource['title'] = f"习题: {question_type}"
            resource['content'] = f"题目：{question}\n\n解析：{answer}\n知识点：{knowledge_tags}\n难度：{difficulty}\n适用场景：{usage_scene}"
            resource['is_image_exercise'] = False
            resource['source'] = source_file
        
        # 添加所有字段到资源对象，以便后续匹配使用
        resource['question'] = question
        resource['answer'] = answer
        resource['difficulty'] = difficulty
        resource['knowledge_tags'] = knowledge_tags
        resource['usage_scene'] = usage_scene
        resource['question_type'] = question_type
    
    def _process_ggb_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理GGB资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        filename = metadata.get('ggb文件名', '')
        chapter = metadata.get('章节', '')
        usage = metadata.get('教学用途', '')
        
        resource['title'] = f"GGB资源: {filename}"
        resource['content'] = f"章节：{chapter}\n教学用途：{usage}"
        resource['filename'] = filename
    
    def _process_syllabus_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理教学大纲资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        chapter = metadata.get('章节', '')
        task = metadata.get('教学任务（教学内容）', '')
        
        resource['title'] = f"教学大纲: {chapter}"
        resource['content'] = f"章节：{chapter}\n教学任务：{task}"
    
    def _process_lesson_plan_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理教案资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        # 教案资源使用标题和内容
        title = metadata.get('title', '')
        content = metadata.get('content', '')
        chapter = metadata.get('章节', '')
        knowledge_tags = metadata.get('知识点标签', '')
        file_topic = metadata.get('文件名主题', '')
        
        resource['title'] = f"教案: {title}"
        resource['content'] = content
        # 传递元数据给主题匹配器
        resource['章节'] = chapter
        resource['知识点标签'] = knowledge_tags
        resource['文件名主题'] = file_topic
        
        # V9.1：提取教案内容特征（教学方法、教学环节等）
        try:
            content_features = self.content_extractor.extract_features(content, title)
            resource['content_features'] = content_features
            resource['teaching_methods'] = content_features.get('teaching_methods', [])
            resource['teaching_stages'] = content_features.get('teaching_stages', [])
            resource['teaching_tools'] = content_features.get('teaching_tools', [])
        except Exception as e:
            # 如果特征提取失败，不影响正常使用
            resource['content_features'] = {}
            resource['teaching_methods'] = []
            resource['teaching_stages'] = []
            resource['teaching_tools'] = []
    
    def _process_courseware_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理课件资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        content = metadata.get('内容', '')
        filename = metadata.get('文件名', '')
        usage = metadata.get('教学用途', '')
        
        resource['title'] = f"课件: {filename}"
        resource['content'] = f"内容：{content}\n教学用途：{usage}"
        resource['filename'] = filename
    
    def _process_lesson_case_resource(self, resource: Dict[str, Any], metadata: Dict[str, Any]):
        """
        处理课例资源
        
        Args:
            resource: 资源对象
            metadata: 元数据
        """
        chapter = metadata.get('章节', '')
        filename = metadata.get('视频文件名/网址', '')
        analysis = metadata.get('分析', '')
        textbook = metadata.get('教材', '')
        
        # 构建描述，优先使用分析内容，如果为空则使用章节和文件名
        content_parts = []
        
        if textbook:
            content_parts.append(f"教材：{textbook}")
        
        if chapter:
            content_parts.append(f"章节：{chapter}")
        
        # 尝试从文件名中提取知识点信息
        if filename and not filename.startswith('http'):
            # 从文件名中提取关键信息
            topic_info = self._extract_topic_from_filename(filename)
            if topic_info:
                content_parts.append(f"知识点：{topic_info}")
        
        if analysis and analysis.strip():
            content_parts.append(f"分析：{analysis}")
        elif filename:
            # 如果分析为空，从文件名中提取关键信息
            content_parts.append(f"视频：{filename}")
        
        resource['title'] = f"课例: {chapter}"
        resource['content'] = "\n".join(content_parts)
        resource['filename'] = filename
    
    def _extract_topic_from_filename(self, filename: str) -> str:
        """
        从课例文件名中提取知识点信息
        
        Args:
            filename: 文件名，如 "4.2.1指数函数的概念.mp4"
            
        Returns:
            提取的知识点信息
        """
        import re
        from pathlib import Path
        
        # 移除文件扩展名
        name = Path(filename).stem
        
        # 移除常见的标记
        name = re.sub(r'【.*?】', '', name)  # 移除【单调性】等标记
        name = re.sub(r'\(.*?\)', '', name)  # 移除括号内容
        name = re.sub(r'\（.*?\）', '', name)  # 移除中文括号内容
        
        # 提取数字编号后的内容（如 "4.2.1指数函数的概念" -> "指数函数的概念"）
        match = re.search(r'^[\d\.]+\s*(.+)$', name)
        if match:
            return match.group(1).strip()
        
        # 如果没有数字编号，直接返回文件名
        return name
    
    def _add_to_category(
        self, 
        classified: Dict[str, List], 
        resource_type: str, 
        resource: Dict[str, Any]
    ):
        """
        将资源添加到对应分类
        
        Args:
            classified: 分类字典
            resource_type: 资源类型
            resource: 资源对象
        """
        category_map = {
            "lesson_plan": "lesson_plan_patterns",
            "visualization": "visualization_examples",
            "exercise": "exercise_resources",
            "courseware": "courseware_resources",
            "lesson_case": "lesson_case_resources",
            "ggb": "ggb_resources",
            "syllabus": "syllabus_resources",
            "theory": "theory_resources"
        }
        
        category = category_map.get(resource_type, "theory_resources")
        # 在资源对象上设置_category属性，供_reclassify_by_relevance方法使用
        resource["_category"] = category
        classified[category].append(resource)
    
    def _balance_resource_distribution(self, resources: List[Dict[str, Any]], core_theme: str, query: str = "") -> List[Dict[str, Any]]:
        """
        平衡资源分布，确保每个主题都有合理数量的核心匹配资源（V8.3新增）
        V14.0改进：添加相关性断层检测，当相关性出现明显断层时只保留高相关性资源
        V31.0改进：通用概念优先排序，优先显示一般性概念资源，然后是具体概念资源
        
        Args:
            resources: 可见资源列表
            core_theme: 核心主题（可能包含多个主题，用逗号分隔）
        
        Returns:
            平衡后的资源列表
        """
        # 解析核心主题
        core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
        
        # V31.0：通用概念优先排序
        # 定义通用概念列表（适用于所有函数类型或数学对象的概念）
        general_concepts = [
            "函数的单调性", "函数的奇偶性", "函数的周期性", "函数的值域", "函数的定义域",
            "函数的图像", "函数的性质", "函数的概念", "函数的应用",
            "函数的零点", "二分法",
            "定义域", "值域", "单调性", "奇偶性", "周期性", "对称性",
            "集合", "不等式", "方程",
            "导数", "积分", "极限",
            "概率", "统计", "期望", "方差",
            "向量", "复数", "数列"
        ]
        
        print(f"   🔍 V31.0 _balance_resource_distribution 被调用，core_theme='{core_theme}', resources数量={len(resources)}")
        
        # 定义通用章节列表（基础概念章节，优先级较高）
        general_chapters = [
            "第三章-函数的概念", "第三章", "函数的概念", "函数的性质",
            "第一章-集合", "第一章", "集合",
            "第二章-不等式", "第二章", "不等式"
        ]
        
        # 检查查询主题是否是通用概念
        is_general_concept_query = any(concept in core_theme for concept in general_concepts)
        print(f"   🔍 V31.0 is_general_concept_query={is_general_concept_query}")
        
        # V46.0改进：对于单调性证明题查询，不使用通用概念优先排序
        is_monotonicity_proof_query = '单调性' in core_theme and '证明题' in query
        if is_monotonicity_proof_query:
            print(f"   🔍 V46.0单调性证明题查询: 不使用通用概念优先排序")
            is_general_concept_query = False
        
        if is_general_concept_query:
            print(f"   🔍 V31.0检测到通用概念查询: '{core_theme}'，启用优先排序")
            
            # 为每个资源计算优先级分数
            for resource in resources:
                source_file = resource.get('source', '') or resource.get('metadata', {}).get('source_file', '')
                
                # 计算优先级分数（越高越优先）
                priority_score = 0
                
                # 1. 来自通用章节的资源优先级更高
                if any(chapter in source_file for chapter in general_chapters):
                    priority_score += 100
                    print(f"      ✅ V31.0通用章节资源: '{resource.get('title', '未知')[:30]}' 来自 {source_file[:50]}")
                
                # 2. 知识点标签不包含特定函数类型的资源优先级更高
                knowledge_tags = resource.get('metadata', {}).get('知识点', '') or resource.get('metadata', {}).get('知识点标签', '')
                # V61.0改进：使用动态配置获取函数类型，避免硬编码
                specific_function_types = self.config_loader.get_all_function_types()
                has_specific_type = any(func_type in knowledge_tags for func_type in specific_function_types)
                if not has_specific_type:
                    priority_score += 50
                else:
                    # 如果包含特定函数类型，降低优先级
                    priority_score -= 30
                
                # 3. 保存优先级分数
                resource['priority_score'] = priority_score
            
            # 按优先级分数和相关性排序
            resources_sorted = sorted(
                resources,
                key=lambda x: (
                    -x.get('priority_score', 0),
                    -x.get('is_core_match', False),
                    -x.get('relevance', 0),
                    -x.get('matched_theme_count', 0)
                )
            )
            
            print(f"   ✅ V31.0优先排序完成，通用概念资源优先")
        else:
            # 非通用概念查询，使用原有排序逻辑
            # 为每个资源检查是否包含核心主题
            for resource in resources:
                # 检查资源是否包含核心主题
                contains_core_theme = False
                if core_theme:
                    # 检查文档内容、标题和元数据是否包含核心主题
                    content = resource.get('content', '') or resource.get('metadata', {}).get('content', '') or ""
                    title = resource.get('title', '') or resource.get('metadata', {}).get('title', '') or ""
                    metadata_str = str(resource) or str(resource.get('metadata', {})) or ""
                    contains_core_theme = core_theme in content or core_theme in title or core_theme in metadata_str
                # 保存是否包含核心主题的标记
                resource['contains_core_theme'] = contains_core_theme
            
            # 按是否包含核心主题和相关性排序
            resources_sorted = sorted(
                resources,
                key=lambda x: (
                    -x.get('contains_core_theme', False),  # 包含核心主题的资源优先
                    -x.get('relevance', 0)  # 然后按相关性排序
                )
            )
        
        # V14.1：相关性断层检测（动态阈值版）
        # resources_sorted 已经在 V31.0 中排序完成
        
        # 检测相关性断层
        if len(resources_sorted) > 1:
            # 获取最高相关性，用于动态计算阈值
            max_relevance = resources_sorted[0].get('relevance', 0)
            
            # V14.3：动态阈值策略（更严格）
            # V93.0改进：调整阈值策略，避免过度过滤
            # - 如果最高相关性 > 80%，阈值设为最高相关性的50%
            # - 如果最高相关性 60-80%，阈值设为最高相关性的45%
            # - 如果最高相关性 40-60%，阈值设为最高相关性的40%
            # - 如果最高相关性 20-40%，阈值设为最高相关性的35%
            # - 如果最高相关性 < 20%，阈值设为最高相关性的30%（最低0.15）
            if max_relevance > 0.80:
                dynamic_threshold = max_relevance * 0.50
            elif max_relevance > 0.60:
                dynamic_threshold = max_relevance * 0.45
            elif max_relevance > 0.40:
                dynamic_threshold = max_relevance * 0.40
            elif max_relevance > 0.20:
                dynamic_threshold = max_relevance * 0.35
            else:
                dynamic_threshold = max_relevance * 0.30
            
            # V93.0改进：降低最小阈值，避免过度过滤
            min_threshold = 0.15
            threshold = max(dynamic_threshold, min_threshold)
            
            print(f"   📊 V14.3动态阈值：最高相关性{max_relevance:.1%}，阈值{threshold:.1%}")
            
            # 计算相邻资源的相关性差距
            gaps = []
            for i in range(len(resources_sorted) - 1):
                current_relevance = resources_sorted[i].get('relevance', 0)
                next_relevance = resources_sorted[i + 1].get('relevance', 0)
                gap = current_relevance - next_relevance
                gaps.append((i, gap))
            
            # 找到最大的断层位置（使用动态阈值）
            significant_gaps = [(i, gap) for i, gap in gaps if gap > threshold]
            
            if significant_gaps:
                # 找到第一个明显断层的位置
                first_gap_idx = significant_gaps[0][0]
                print(f"   📊 V14.1检测到相关性断层：位置{first_gap_idx}，差距{significant_gaps[0][1]:.1%}")
                print(f"   📊 断层前相关性：{resources_sorted[first_gap_idx].get('relevance', 0):.1%}")
                print(f"   📊 断层后相关性：{resources_sorted[first_gap_idx + 1].get('relevance', 0):.1%}")
                
                # 只保留断层前的资源
                high_relevance_resources = resources_sorted[:first_gap_idx + 1]
                print(f"   ✅ V14.1只保留高相关性资源：{len(high_relevance_resources)}个（原{len(resources)}个）")
                
                # 对保留的资源进行排序（V31.0：保留优先级分数排序）
                high_relevance_resources.sort(
                    key=lambda x: (
                        -x.get('priority_score', 0),
                        -x.get('is_core_match', False),
                        -x.get('relevance', 0),
                        -x.get('matched_theme_count', 0),
                        -x.get('theme_boost', 0)
                    )
                )
                return high_relevance_resources
        
        # 如果没有检测到断层，也只保留相关性高于阈值的资源
        max_relevance = resources_sorted[0].get('relevance', 0) if resources_sorted else 0
        
        # V61.0改进：提高阈值，确保返回资源的相关性
        if max_relevance > 0.80:
            min_relevance_threshold = max_relevance * 0.50
        elif max_relevance > 0.60:
            min_relevance_threshold = max_relevance * 0.45
        elif max_relevance > 0.40:
            min_relevance_threshold = max_relevance * 0.40
        else:
            min_relevance_threshold = max_relevance * 0.35
        
        # V61.0改进：提高最小阈值，确保资源相关性
        min_threshold = 0.30
        min_relevance_threshold = max(min_relevance_threshold, min_threshold)
        
        filtered_resources = [r for r in resources_sorted if r.get('relevance', 0) >= min_relevance_threshold]
        if len(filtered_resources) < len(resources_sorted):
            print(f"   ✅ V14.1过滤低相关性资源：保留{len(filtered_resources)}个（原{len(resources_sorted)}个），阈值{min_relevance_threshold:.1%}")
            # 对过滤后的资源进行排序（V31.0：保留优先级分数排序）
            filtered_resources.sort(
                key=lambda x: (
                    -x.get('priority_score', 0),
                    -x.get('is_core_match', False),
                    -x.get('relevance', 0),
                    -x.get('matched_theme_count', 0),
                    -x.get('theme_boost', 0)
                )
            )
            return filtered_resources
        
        # 多主题查询，平衡资源分布
        if len(core_themes) > 1:
            print(f"   🔄 多主题资源分布平衡，主题: {core_themes}")
            
            # 按主题分组资源
            theme_resources = {theme: [] for theme in core_themes}
            other_resources = []
            
            # 只使用经过动态阈值过滤的资源
            filtered_resources = resources_sorted if 'high_relevance_resources' not in locals() else high_relevance_resources
            
            print(f"   🔍 多主题资源分布平衡：filtered_resources 数量: {len(filtered_resources)}")
            
            # 检测是否是函数性质主题查询
            is_function_property_query = any(theme in ["函数的单调性", "函数的奇偶性", "函数的周期性"] for theme in core_themes)
            
            for resource in filtered_resources:
                matched_themes = resource.get('matched_themes', [])
                assigned_themes = []
                
                print(f"   🔍 检查资源 '{resource.get('title', '未知')}' 的 matched_themes: {matched_themes}")
                
                # V25.3改进：资源应该分配到所有匹配的主题，而不是只分配到第一个
                for theme in core_themes:
                    if any(theme.strip() == t.strip() for t in matched_themes):
                        theme_resources[theme].append(resource)
                        assigned_themes.append(theme)
                        print(f"      ✅ 分配到主题 '{theme}'")
                    # V61.0改进：对于函数性质主题，根据资源内容进行更宽松的匹配
                    elif is_function_property_query:
                        resource_content = resource.get('content', '') or resource.get('doc', '')
                        resource_source = resource.get('source', '')
                        knowledge_tags = resource.get('知识点', '') or resource.get('metadata', {}).get('知识点', '') or resource.get('metadata', {}).get('知识点标签', '')
                        
                        # 对于函数性质主题，检查资源内容、来源或知识点标签是否包含相关关键词
                        if theme == "函数的单调性":
                            monotonicity_keywords = ["单调性", "单调", "增函数", "减函数", "单调递增", "单调递减"]
                            if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in monotonicity_keywords):
                                theme_resources[theme].append(resource)
                                assigned_themes.append(theme)
                                print(f"      ✅ 函数性质宽松匹配：分配到主题 '{theme}'")
                        elif theme == "函数的奇偶性":
                            parity_keywords = ["奇偶性", "奇函数", "偶函数", "对称性", "对称"]
                            if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in parity_keywords):
                                theme_resources[theme].append(resource)
                                assigned_themes.append(theme)
                                print(f"      ✅ 函数性质宽松匹配：分配到主题 '{theme}'")
                        elif theme == "函数的周期性":
                            periodicity_keywords = ["周期性", "周期", "周期函数"]
                            if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in periodicity_keywords):
                                theme_resources[theme].append(resource)
                                assigned_themes.append(theme)
                                print(f"      ✅ 函数性质宽松匹配：分配到主题 '{theme}'")
                
                if not assigned_themes:
                    other_resources.append(resource)
                    print(f"      ⚠️ 未分配到任何主题")
            
            # 统计每个主题的资源数量
            theme_counts = {theme: len(resources) for theme, resources in theme_resources.items()}
            print(f"   📊 各主题资源数量: {theme_counts}")
            
            # V21.1改进：确保每个主题至少分配到一定数量的资源
            # 如果某个主题资源较少，降低其相关性阈值，允许更多资源通过
            # V23.2改进：对一次函数使用更低的阈值
            min_resources_per_theme = 2  # 每个主题至少2个资源
            for theme in core_themes:
                if len(theme_resources[theme]) < min_resources_per_theme:
                    print(f"   ⚠️ 主题 '{theme}' 资源不足 ({len(theme_resources[theme])}个)，尝试从其他资源补充...")
                    # 从other_resources中查找可能匹配该主题的资源
                    for resource in other_resources[:]:
                        # 检查资源内容是否包含该主题关键词
                        resource_content = resource.get('content', '') or resource.get('doc', '')
                        resource_source = resource.get('source', '')
                        knowledge_tags = resource.get('知识点', '') or resource.get('metadata', {}).get('知识点', '') or resource.get('metadata', {}).get('知识点标签', '')
                        
                        # V23.2改进：对一次函数使用更宽松的匹配
                        if theme == '一次函数':
                            # 扩展一次函数匹配关键词
                            linear_keywords = ['一次函数', '线性函数', '直线', '斜率', '截距', '正比例函数', 'y=kx', 'y = kx', 'y=ax', 'y = ax', 'y=x', 'y = x', '线性关系']
                            if any(keyword in resource_content for keyword in linear_keywords):
                                theme_resources[theme].append(resource)
                                other_resources.remove(resource)
                                print(f"      ✅ V23.2补充一次函数资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
                                if len(theme_resources[theme]) >= min_resources_per_theme:
                                    break
                        # V61.0改进：对于函数性质主题，使用更宽松的匹配
                        elif is_function_property_query:
                            if theme == "函数的单调性":
                                monotonicity_keywords = ["单调性", "单调", "增函数", "减函数", "单调递增", "单调递减"]
                                if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in monotonicity_keywords):
                                    theme_resources[theme].append(resource)
                                    other_resources.remove(resource)
                                    print(f"      ✅ 补充函数性质资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
                                    if len(theme_resources[theme]) >= min_resources_per_theme:
                                        break
                            elif theme == "函数的奇偶性":
                                parity_keywords = ["奇偶性", "奇函数", "偶函数", "对称性", "对称"]
                                if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in parity_keywords):
                                    theme_resources[theme].append(resource)
                                    other_resources.remove(resource)
                                    print(f"      ✅ 补充函数性质资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
                                    if len(theme_resources[theme]) >= min_resources_per_theme:
                                        break
                            elif theme == "函数的周期性":
                                periodicity_keywords = ["周期性", "周期", "周期函数"]
                                if any(keyword in resource_content or keyword in resource_source or keyword in knowledge_tags for keyword in periodicity_keywords):
                                    theme_resources[theme].append(resource)
                                    other_resources.remove(resource)
                                    print(f"      ✅ 补充函数性质资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
                                    if len(theme_resources[theme]) >= min_resources_per_theme:
                                        break
                        elif theme in resource_content:
                            theme_resources[theme].append(resource)
                            other_resources.remove(resource)
                            print(f"      ✅ 补充资源到主题 '{theme}': {resource.get('title', '未知')[:30]}...")
                            if len(theme_resources[theme]) >= min_resources_per_theme:
                                break
            
            # 重新统计
            theme_counts = {theme: len(resources) for theme, resources in theme_resources.items()}
            print(f"   📊 补充后各主题资源数量: {theme_counts}")
            
            # V24.1改进：如果一次函数资源仍然不足，从所有资源中强制补充
            if '一次函数' in core_themes and len(theme_resources.get('一次函数', [])) < min_resources_per_theme:
                print(f"   ⚠️ V24.1: 一次函数资源仍然不足，从所有资源中强制补充...")
                for resource in resources_sorted[:]:  # 从所有排序后的资源中查找
                    if resource in theme_resources.get('一次函数', []):
                        continue
                    resource_content = resource.get('content', '') or resource.get('doc', '')
                    knowledge_tags = resource.get('metadata', {}).get('知识点', '')
                    # 检查知识点标签或内容是否包含一次函数
                    if '一次函数' in knowledge_tags or '一次函数' in resource_content:
                        theme_resources['一次函数'].append(resource)
                        print(f"      ✅ V24.1强制补充一次函数资源: {resource.get('title', '未知')[:30]}...")
                        if len(theme_resources['一次函数']) >= min_resources_per_theme:
                            break
                # 更新统计
                theme_counts = {theme: len(resources) for theme, resources in theme_resources.items()}
                print(f"   📊 V24.1强制补充后各主题资源数量: {theme_counts}")
            
            # 计算每个主题的目标数量（取平均值的1.5倍，确保每个主题都有足够资源）
            total_visible = len(filtered_resources)
            target_per_theme = max(3, int(total_visible / len(core_themes) * 1.5))
            print(f"   🎯 每个主题目标数量: {target_per_theme}")
            
            # 为每个主题选择资源，并按相关性排序
            # V9.1：获取查询的内容特征（用于内容匹配评分）
            query_features = getattr(self, '_current_query_features', {})
            
            for theme in core_themes:
                theme_list = theme_resources[theme]
                
                # V9.1：计算内容匹配得分并更新相关性
                if query_features.get('has_content_requirement'):
                    print(f"   🔍 V9.1为主题 '{theme}' 计算内容匹配得分...")
                    for resource in theme_list:
                        if 'content_features' in resource:
                            content_score = self.content_extractor.calculate_content_match_score(
                                resource['content_features'],
                                query_features
                            )
                            # 将内容匹配得分融入相关性
                            original_relevance = resource.get('relevance', 0)
                            # 内容匹配得分占30%权重
                            resource['relevance'] = original_relevance * 0.7 + content_score * 0.3
                            resource['content_match_score'] = content_score
                            resource['original_relevance'] = original_relevance
                
                # 按相关性排序（V9.1：现在包含内容匹配得分）
                theme_list.sort(
                    key=lambda x: (
                        -x.get('is_core_match', False),
                        -x.get('relevance', 0),
                        -x.get('matched_theme_count', 0),
                        -x.get('theme_boost', 0)
                    )
                )
                
                print(f"   ✅ 主题 '{theme}': 共 {len(theme_list)} 个资源")
            
            # V8.3改进：使用轮询方式交替选择各主题的资源，提升用户体验
            balanced_resources = []
            theme_indices = {theme: 0 for theme in core_themes}
            used_resources = set()  # 跟踪已使用的资源
            
            # 计算每个主题的目标数量
            target_per_theme = max(3, int(total_visible / len(core_themes) * 1.5))
            
            # 确保每个主题至少有一个资源
            min_resources_per_theme = 1
            
            # 轮询选择资源，直到达到目标数量或资源耗尽
            round_num = 0
            while len(balanced_resources) < total_visible:
                added_in_round = 0
                
                for theme in core_themes:
                    theme_list = theme_resources[theme]
                    idx = theme_indices[theme]
                    
                    # 检查是否还有资源且未达到该主题的目标数量
                    # 对于多主题查询，确保每个主题至少有一个资源
                    while idx < len(theme_list) and (idx < target_per_theme or len(balanced_resources) < len(core_themes)):
                        resource = theme_list[idx]
                        resource_id = f"{resource.get('title', '')}_{resource.get('source', '')}"
                        
                        # 检查资源是否已被使用
                        if resource_id not in used_resources:
                            balanced_resources.append(resource)
                            used_resources.add(resource_id)
                            theme_indices[theme] = idx + 1
                            added_in_round += 1
                            print(f"      ✅ 轮询选择：主题 '{theme}' 资源 {idx+1}: {resource.get('title', '未知')}")
                            break
                        else:
                            # 跳过已使用的资源，尝试下一个
                            idx += 1
                            theme_indices[theme] = idx
                
                # 如果本轮没有添加任何资源，说明所有主题的资源都已耗尽
                if added_in_round == 0:
                    break
                
                round_num += 1
            
            print(f"   🔄 轮询选择完成: {round_num} 轮，共选择 {len(balanced_resources)} 个资源")
            
            # 计算相关性阈值（使用V14.3动态阈值策略，更严格）
            max_relevance = balanced_resources[0].get('relevance', 0) if balanced_resources else 0
            # V16.0改进：进一步放宽阈值，确保返回更多资源
            if max_relevance > 0.80:
                min_relevance_threshold = 0.50 * max_relevance  # 从0.60降低到0.50
            elif max_relevance > 0.60:
                min_relevance_threshold = 0.40 * max_relevance  # 从0.50降低到0.40
            elif max_relevance > 0.40:
                min_relevance_threshold = 0.30 * max_relevance  # 从0.40降低到0.30
            else:
                min_relevance_threshold = 0.20 * max_relevance  # 从0.30降低到0.20
            min_relevance_threshold = max(min_relevance_threshold, 0.20)  # 从0.30降低到0.20
            
            # 过滤核心主题资源和其他资源，只保留相关性高于阈值的
            filtered_balanced_resources = [r for r in balanced_resources if r.get('relevance', 0) >= min_relevance_threshold]
            filtered_other_resources = [r for r in other_resources if r.get('relevance', 0) >= min_relevance_threshold]
            
            # 计算剩余空间（最多添加总可见资源的1/3作为其他资源）
            remaining_space = max(0, total_visible - len(filtered_balanced_resources))
            max_other_count = max(0, int(total_visible * 0.33))
            other_count = min(len(filtered_other_resources), remaining_space, max_other_count)
            
            # 合并资源
            balanced_resources = filtered_balanced_resources + filtered_other_resources[:other_count]
            
            # 按相关性重新排序
            balanced_resources.sort(key=lambda x: x.get('relevance', 0), reverse=True)
            
            print(f"   ✅ 平衡完成: {len(balanced_resources)} 个资源（核心主题: {len(filtered_balanced_resources)}个，其他资源: {other_count}个，过滤后）")
            
            return balanced_resources
        else:
            # 单主题查询，按原有排序逻辑
            resources_sorted.sort(
                key=lambda x: (
                    -x.get('is_core_match', False),
                    -x.get('relevance', 0),
                    -x.get('matched_theme_count', 0),
                    -x.get('theme_boost', 0)
                )
            )
            return resources_sorted
    
    def _reclassify_by_relevance(self, all_resources: List[Dict[str, Any]], core_theme: str = "") -> Dict[str, Any]:
        """
        按相关性重新分类资源（V8.1新增）
        V55.0改进：为每种资源类型单独计算阈值，避免组合查询时某些资源类型被过滤
        
        Args:
            all_resources: 已按相关性排序的所有资源列表
            core_theme: 核心主题
        
        Returns:
            分类后的资源字典（按相关性分组）
        """
        # 初始化分类
        classified = {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "exercise_resources": [],
            "visualization_examples": [],
            "general_resources": [],
            "courseware_resources": [],
            "lesson_case_resources": [],
            "ggb_resources": [],
            "syllabus_resources": [],
            "_hidden_resources": [],
            "_hidden_count": 0,
            "_total_count": 0
        }
        
        # V55.0改进：为每种资源类型单独计算阈值
        # 首先按资源类型分组
        resources_by_category = {}
        for resource in all_resources:
            category = resource.get("_category")
            
            # 如果没有_category属性，尝试从资源类型推断
            if not category:
                resource_type = resource.get('metadata', {}).get('resource_type', '')
                category_map = {
                    "lesson_plan": "lesson_plan_patterns",
                    "visualization": "visualization_examples",
                    "exercise": "exercise_resources",
                    "courseware": "courseware_resources",
                    "lesson_case": "lesson_case_resources",
                    "ggb": "ggb_resources",
                    "syllabus": "syllabus_resources",
                    "theory": "theory_resources"
                }
                category = category_map.get(resource_type, "theory_resources")
            
            if category not in resources_by_category:
                resources_by_category[category] = []
            resources_by_category[category].append(resource)
        
        # V55.0改进：为每种资源类型单独计算阈值
        # V61.0改进：提高阈值下限，确保资源相关性
        category_thresholds = {}
        for category, resources in resources_by_category.items():
            if resources:
                # 按相关性排序
                resources_sorted = sorted(resources, key=lambda x: -x.get('relevance', 0))
                max_relevance = resources_sorted[0].get('relevance', 0)
                
                # 根据最高相关性动态调整阈值
                if max_relevance > 0.80:
                    threshold = 0.60 * max_relevance
                elif max_relevance > 0.60:
                    threshold = 0.50 * max_relevance
                elif max_relevance > 0.40:
                    threshold = 0.40 * max_relevance
                elif max_relevance > 0.20:
                    threshold = 0.30 * max_relevance
                else:
                    threshold = 0.35 * max_relevance
                
                # V61.0改进：提高下限，确保资源相关性
                threshold = max(threshold, 0.30)
                
                category_thresholds[category] = threshold
                print(f"   📊 V55.0 {category}阈值：最高相关性{max_relevance:.1%}，阈值{threshold:.1%}")
        
        # V55.0改进：使用各自资源类型的阈值进行过滤
        for resource in all_resources:
            relevance = resource.get('relevance', 0)
            category = resource.get("_category")
            
            # 如果没有_category属性，尝试从资源类型推断
            if not category:
                resource_type = resource.get('metadata', {}).get('resource_type', '')
                category_map = {
                    "lesson_plan": "lesson_plan_patterns",
                    "visualization": "visualization_examples",
                    "exercise": "exercise_resources",
                    "courseware": "courseware_resources",
                    "lesson_case": "lesson_case_resources",
                    "ggb": "ggb_resources",
                    "syllabus": "syllabus_resources",
                    "theory": "theory_resources"
                }
                category = category_map.get(resource_type, "theory_resources")
            
            # 检查资源是否包含核心主题
            metadata = resource.get('metadata', {})
            content = resource.get('content', '') or metadata.get('content', '')
            title = metadata.get('title', '')
            contains_core_theme = core_theme and (core_theme in content or core_theme in title or core_theme in str(metadata))
            
            # 使用各自资源类型的阈值
            threshold = category_thresholds.get(category, 0.10)
            
            if relevance >= threshold or contains_core_theme:
                if category in classified:
                    classified[category].append(resource)
                    if contains_core_theme and relevance < threshold:
                        print(f"   ✅ 保留（包含核心主题）：'{title}' (相关性: {relevance:.2f} < {threshold:.2f})")
            else:
                # 低相关性资源放入隐藏资源
                classified["_hidden_resources"].append(resource)
        
        # 更新计数
        classified["_hidden_count"] = len(classified["_hidden_resources"])
        classified["_total_count"] = len(all_resources)
        
        total_kept = sum(len(resources) for key, resources in classified.items() 
                        if isinstance(resources, list) and not key.startswith('_'))
        print(f"   ✅ V55.0分类完成：保留{total_kept}个资源，隐藏{classified['_hidden_count']}个资源")
        
        return classified
    
    def _check_grade_match(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V28.0：应用年级筛选
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
        
        Returns:
            筛选结果字典，包含pass和reason
        """
        source_file = metadata.get('source_file', '')
        
        # 使用年级元数据增强器推断资源的年级
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        
        if not resource_grade:
            # 无法推断年级，默认通过
            return {'pass': True, 'reason': '无法推断资源年级'}
        
        # 检查年级是否匹配
        target_grade = grade_info.get('grade')
        target_grade_level = grade_info.get('grade_level')
        
        if resource_grade.get('grade') == target_grade:
            # 年级完全匹配
            return {'pass': True, 'reason': f'年级匹配: {target_grade}'}
        
        # V53.0改进：检查资源年级是否包含目标年级
        # 例如："高一上学期"包含"高一"，"高一下学期"包含"高一"
        resource_grade_str = resource_grade.get('grade', '')
        if target_grade and target_grade in resource_grade_str:
            return {'pass': True, 'reason': f'年级包含匹配: {resource_grade_str}包含{target_grade}'}
        
        # V53.1改进：检查是否是跨年级主题的查询
        # 某些主题（如函数、概率、立体几何等）在高中各年级都有学习，允许更宽松的年级匹配
        is_cross_grade_topic = False
        knowledge_tags = metadata.get('知识点标签', '')
        title = metadata.get('title', '')
        content = metadata.get('题干', '') + metadata.get('解析', '')
        
        # V53.1改进：使用动态生成的主题关键词，而不是硬编码
        # 这样当资源库扩展时，系统也能自动适应
        for keyword in self.all_theme_keywords:
            if keyword in knowledge_tags or keyword in title or keyword in content:
                is_cross_grade_topic = True
                break
        
        # 对于跨年级主题，允许更宽松的年级匹配
        if is_cross_grade_topic:
            # 跨年级主题允许相差2个级别（如高一和高二）
            resource_grade_level = resource_grade.get('grade_level')
            if resource_grade_level and target_grade_level:
                level_diff = abs(resource_grade_level - target_grade_level)
                if level_diff <= 2:
                    return {'pass': True, 'reason': f'跨年级主题: 允许查看{resource_grade.get("grade")}的内容'}
        
        # 检查年级级别是否匹配（允许一定的灵活性）
        resource_grade_level = resource_grade.get('grade_level')
        if resource_grade_level and target_grade_level:
            # 对于高三查询，允许查看高一、高二的内容（高考复习需要）
            if target_grade_level >= 14:  # 高三
                if resource_grade_level <= 14:  # 高一、高二、高三
                    return {'pass': True, 'reason': f'高三复习: 允许查看{resource_grade.get("grade")}的内容'}
            # 对于其他年级，允许相邻年级
            elif abs(resource_grade_level - target_grade_level) <= 1:
                return {'pass': True, 'reason': f'年级相近: {resource_grade.get("grade")} vs {target_grade}'}
        
        # 年级不匹配
        return {
            'pass': False,
            'reason': f'年级不匹配: 资源是{resource_grade.get("grade")}，查询要求{target_grade}'
        }
    
    def _apply_subjective_intent_filter(self, metadata: Dict[str, Any], subjective_intent: Dict[str, Any], is_vague_query: bool = False) -> Dict[str, Any]:
        """
        V28.0：应用主观意图筛选（V32.0改进：支持灵活匹配）
        
        Args:
            metadata: 资源元数据
            subjective_intent: 主观意图信息
            is_vague_query: 是否是宽泛查询
        
        Returns:
            筛选结果字典，包含pass、reason和score_adjustment
        """
        # 获取资源的难度
        difficulty_str = metadata.get('难度（1-5）', '') or metadata.get('难度', '') or metadata.get('difficulty', '3')
        try:
            difficulty = int(difficulty_str)
        except (ValueError, TypeError):
            # 尝试从文本难度转换为数字
            difficulty_map = {
                '基础': 1,
                '简单': 1,
                '中等': 2,
                '一般': 2,
                '普通': 2,
                '难': 3,
                '困难': 3,
                '拔高': 4,
                '挑战': 4,
                '压轴': 5
            }
            if isinstance(difficulty_str, str):
                for key, value in difficulty_map.items():
                    if key in difficulty_str:
                        difficulty = value
                        break
                else:
                    difficulty = 3
            else:
                difficulty = 3
        
        # 获取主观意图的难度范围
        difficulty_range = subjective_intent.get('difficulty_range')
        
        if difficulty_range:
            min_difficulty, max_difficulty = difficulty_range
            
            # V32.0：宽泛查询时，放宽难度筛选
            if is_vague_query:
                # 宽泛查询 - 允许一定范围内的偏差
                tolerance = 1  # 允许1级的偏差
                
                if difficulty < min_difficulty - tolerance:
                    # 难度太低，但不过滤，只降低相关性
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}略低于要求，但宽泛查询允许',
                        'score_adjustment': 0.6
                    }
                elif difficulty > max_difficulty + tolerance:
                    # 难度太高，但不过滤，只降低相关性
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}略高于要求，但宽泛查询允许',
                        'score_adjustment': 0.6
                    }
                else:
                    # 难度在可接受范围内
                    target_difficulty = (min_difficulty + max_difficulty) / 2
                    diff_from_target = abs(difficulty - target_difficulty)
                    score_adjustment = 1.0 - (diff_from_target / 3.0)  # 最多降低33%
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}符合要求',
                        'score_adjustment': max(0.7, score_adjustment)
                    }
            else:
                # 具体查询 - 严格难度筛选
                if difficulty < min_difficulty:
                    return {
                        'pass': False,
                        'reason': f'难度{difficulty}低于要求范围[{min_difficulty}-{max_difficulty}]'
                    }
                elif difficulty > max_difficulty:
                    return {
                        'pass': False,
                        'reason': f'难度{difficulty}高于要求范围[{min_difficulty}-{max_difficulty}]'
                    }
                else:
                    target_difficulty = (min_difficulty + max_difficulty) / 2
                    diff_from_target = abs(difficulty - target_difficulty)
                    score_adjustment = 1.0 - (diff_from_target / 2.0)
                    return {
                        'pass': True,
                        'reason': f'难度{difficulty}在要求范围内',
                        'score_adjustment': max(0.5, score_adjustment)
                    }
        
        # 没有难度要求，默认通过
        return {'pass': True, 'reason': '无难度要求'}
    
    def _is_vague_grade_query(self, query: str, grade_info: Dict[str, Any]) -> bool:
        """
        V32.0：判断是否是宽泛的年级查询
        
        宽泛查询的特征：
        - 只有年级关键词（如"高三数学"、"高一"）
        - 没有具体的主题或知识点
        - 没有明确的难度要求
        
        Args:
            query: 用户查询
            grade_info: 年级信息
            
        Returns:
            是否是宽泛查询
        """
        if not query or not grade_info:
            return False
        
        query_lower = query.lower()
        
        # 1. 检查是否有具体的主题关键词
        theme_keywords = [
            '函数', '方程', '不等式', '集合', '向量', '复数', '数列', '导数', '积分',
            '三角', '指数', '对数', '二次', '一次', '幂函数', '圆锥曲线', '立体几何',
            '概率', '统计', '排列组合', '二项式'
        ]
        has_theme = any(keyword in query_lower for keyword in theme_keywords)
        
        # 2. 检查是否有明确的难度要求
        difficulty_keywords = ['基础', '简单', '中等', '提高', '难题', '拔高', '冲刺', '竞赛']
        has_difficulty = any(keyword in query_lower for keyword in difficulty_keywords)
        
        # 3. 检查是否有具体的知识点
        knowledge_keywords = ['概念', '性质', '图像', '单调性', '奇偶性', '周期性', '定义域', '值域']
        has_knowledge = any(keyword in query_lower for keyword in knowledge_keywords)
        
        # 4. 检查是否有资源类型要求
        type_keywords = ['教案', '习题', '课件', '课例', '真题', '模拟']
        has_type = any(keyword in query_lower for keyword in type_keywords)
        
        # 宽泛查询 = 只有年级，没有其他具体要求
        is_vague = not (has_theme or has_difficulty or has_knowledge or has_type)
        
        # V52.0改进：对于高三查询，放宽年级筛选条件
        # 高三学生需要复习所有年级的知识，所以即使包含主题，也应该被认为是宽泛查询
        if grade_info.get('grade') == '高三':
            print(f"   🔍 V52.0高三查询: 放宽年级筛选条件")
            is_vague = True
        
        if is_vague:
            print(f"   🔍 V32.0检测到宽泛查询: 年级={grade_info.get('grade')}, 无具体主题/难度/类型要求")
        else:
            print(f"   🔍 V32.0检测到具体查询: 主题={has_theme}, 难度={has_difficulty}, 知识点={has_knowledge}, 类型={has_type}")
        
        return is_vague
    
    def _apply_flexible_grade_filter(self, metadata: Dict[str, Any], grade_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        V32.0：应用灵活的年级筛选（用于宽泛查询）
        
        策略：
        - 宽泛查询时，放宽年级筛选，允许各年级相关内容
        - 优先返回查询年级的内容，但也允许其他年级的相关内容
        - 通过调整相关性得分来体现优先级
        
        Args:
            metadata: 资源元数据
            grade_info: 年级信息
            
        Returns:
            筛选结果字典
        """
        source_file = metadata.get('source_file', '')
        
        # 使用年级元数据增强器推断资源的年级
        resource_grade = self.grade_enricher.infer_grade_from_path(source_file)
        
        if not resource_grade:
            # 无法推断年级，默认通过
            return {'pass': True, 'reason': '无法推断资源年级', 'score_adjustment': 0.8}
        
        target_grade = grade_info.get('grade')
        target_grade_level = grade_info.get('grade_level')
        resource_grade_level = resource_grade.get('grade_level')
        
        # 完全匹配 - 最高优先级
        if resource_grade.get('grade') == target_grade:
            return {'pass': True, 'reason': f'年级完全匹配: {target_grade}', 'score_adjustment': 1.0}
        
        # 高三查询 - 允许高一、高二、高三的所有内容（复习需要）
        if target_grade_level and target_grade_level >= 14:  # 高三
            if resource_grade_level:
                if resource_grade_level <= 14:  # 高一、高二、高三
                    # 根据距离调整得分
                    level_diff = abs(target_grade_level - resource_grade_level)
                    score_adjustment = max(0.6, 1.0 - level_diff * 0.15)  # 最多降低40%
                    return {
                        'pass': True, 
                        'reason': f'高三复习: 包含{resource_grade.get("grade")}内容',
                        'score_adjustment': score_adjustment
                    }
        
        # 其他年级查询 - 允许相邻年级的内容
        if target_grade_level and resource_grade_level:
            level_diff = abs(resource_grade_level - target_grade_level)
            if level_diff <= 2:  # 允许相差2个级别（如高一和高二）
                score_adjustment = max(0.5, 1.0 - level_diff * 0.2)  # 最多降低60%
                return {
                    'pass': True,
                    'reason': f'年级相近: {resource_grade.get("grade")} vs {target_grade}',
                    'score_adjustment': score_adjustment
                }
        
        # 年级相差太大，降低相关性但不完全过滤
        return {
            'pass': True,
            'reason': f'年级较远但仍相关: {resource_grade.get("grade")} vs {target_grade}',
            'score_adjustment': 0.4  # 大幅降低相关性
        }
    
    def _get_empty_result(self) -> Dict[str, Any]:
        """
        获取空的检索结果
        
        Returns:
            空结果字典
        """
        return {
            "theory_resources": [],
            "lesson_plan_patterns": [],
            "exercise_resources": [],
            "visualization_examples": [],
            "general_resources": [],
            "courseware_resources": [],
            "lesson_case_resources": [],
            "ggb_resources": [],
            "syllabus_resources": [],
            "_hidden_resources": [],
            "_hidden_count": 0,
            "_total_count": 0
        }
    
    def _extract_query_conditions(self, query: str) -> Dict[str, str]:
        """
        V49.0改进：从查询中提取多维度条件
        
        Args:
            query: 用户查询
        
        Returns:
            包含各维度条件的字典
        """
        conditions = {
            'knowledge_points': [],
            'question_type': '',
            'difficulty': '',
            'grade': '',
            'exam_form': '',
            'quantity': 0,
            'intent': '',  # 新增：查询意图
            'context': ''   # 新增：查询上下文
        }
        
        # 1. 提取查询意图
        intent_patterns = [
            ('练习', ['练习题', '习题', '题目', '测试题', '题']),
            ('学习', ['学习', '了解', '掌握', '理解', '认识']),
            ('教学', ['教学', '教案', '课件', '教学设计', '教学方案']),
            ('复习', ['复习', '巩固', '回顾', '总结']),
            ('备考', ['备考', '冲刺', '模拟', '真题']),
            ('比较', ['比较', '对比', '区别', '联系', '异同']),
            ('应用', ['应用', '实际应用', '应用题', '实践'])
        ]
        
        for intent, patterns in intent_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['intent'] = intent
                    break
            if conditions['intent']:
                break
        
        # 2. 提取数量要求
        import re
        quantity_patterns = [
            (r'(\d+)道', True),
            (r'(\d+)题', True),
            (r'(\d+)个', True),
            (r'(\d+)道题', True),
            (r'几道', False),
            (r'一些', False),
            (r'几个', False),
            (r'少量', False),
            (r'多个', False),
            (r'几个', False)
        ]
        
        for pattern, has_group in quantity_patterns:
            match = re.search(pattern, query)
            if match:
                if has_group and match.group(1):
                    try:
                        conditions['quantity'] = int(match.group(1))
                    except:
                        conditions['quantity'] = 5
                else:
                    conditions['quantity'] = 5
                break
        
        # 3. 提取年级
        grade_patterns = [
            ('高一', ['高一', '高1', '高一上', '高一下', '高中一年级']),
            ('高二', ['高二', '高2', '高二上', '高二下', '高中二年级']),
            ('高三', ['高三', '高3', '高三上', '高三下', '高中三年级']),
            ('初中', ['初中', '初一', '初二', '初三', '初中一年级', '初中二年级', '初中三年级'])
        ]
        
        for grade, patterns in grade_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['grade'] = grade
                    break
            if conditions['grade']:
                break
        
        # 4. 提取难度
        difficulty_patterns = [
            ('基础', ['基础', '简单', '刚学', '入门', '初级', '容易', '基础题', '简单题', '简单练习', '基础练习']),
            ('中等', ['中等', '一般', '普通', '常见', '适中', '中等题', '中等难度', '一般难度']),
            ('拔高', ['拔高', '难', '困难', '挑战', '压轴', '难题', '提高', '进阶', '综合', '困难题', '高难度'])
        ]
        
        for difficulty, patterns in difficulty_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['difficulty'] = difficulty
                    print(f"   📝 识别到难度: {difficulty} (匹配关键词: {pattern})")
                    break
            if conditions['difficulty']:
                break
        
        # 5. 提取考查形式
        exam_form_patterns = [
            ('性质', ['性质', '单调性', '奇偶性', '周期性', '对称性', '定义域', '值域', '图像', '零点']),
            ('应用', ['应用', '实际应用', '应用题', '综合应用', '生活应用', '经济应用', '物理应用']),
            ('证明', ['证明', '证明题', '求证', '推导', '证明方法', '数学归纳法']),
            ('计算', ['计算', '计算题', '求解', '求值', '计算方法', '运算']),
            ('最值', ['最值', '最大值', '最小值', '极值', '最值问题', '取值范围', '值域问题']),
            ('单调性', ['单调性', '单调递增', '单调递减', '单调区间', '单调性证明']),
            ('奇偶性', ['奇偶性', '奇函数', '偶函数', '奇偶性判断'])
        ]
        
        for exam_form, patterns in exam_form_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['exam_form'] = exam_form
                    print(f"   📝 V100.0识别到考查形式: {exam_form} (匹配关键词: {pattern})")
                    break
            if conditions['exam_form']:
                break
        
        # 6. 提取题目类型
        # V95.0改进：增强题目类型识别，特别是应用题
        question_type_patterns = [
            ('选择题', ['选择题', '单选题', '多选题', '选择', '单选', '多选']),
            ('证明题', ['证明题', '求证', '证明', '证明题', '推导题']),
            ('填空题', ['填空题', '填空', '填空题']),
            ('解答题', ['解答题', '计算题', '解答', '计算']),
            ('应用题', ['应用题', '实际背景', '实际问题', '应用场景', '应用问题', '实际应用']),
            ('判断题', ['判断题', '判断', '是非题']),
            ('简答题', ['简答题', '简答']),
            ('开放题', ['开放题', '开放性问题'])
        ]
        
        for qtype, patterns in question_type_patterns:
            for pattern in patterns:
                if pattern in query:
                    conditions['question_type'] = qtype
                    print(f"   📝 V95.0识别到题目类型: {qtype} (匹配关键词: {pattern})")
                    break
            if conditions['question_type']:
                break
        
        # 6. 提取知识点（使用现有的主题提取逻辑）
        core_theme = self._extract_core_theme(query)
        if core_theme:
            conditions['knowledge_points'] = [t.strip() for t in core_theme.split(',') if t.strip()]
        
        print(f"   ✅ V49.0提取查询条件: {conditions}")
        return conditions
    
    def _extract_resource_types_from_query(self, query: str) -> List[str]:
        """
        V61.0改进：从查询中自动识别资源类型
        
        Args:
            query: 用户查询
        
        Returns:
            资源类型列表
        """
        resource_types = []
        resource_type_keywords = {
            "教案": ["教案", "教学设计", "教学方案", "教学计划", "备课", "导学案", "详案", "简案", "教学反思", "核心素养"],
            "教学大纲": ["教学大纲", "大纲", "课程标准", "教学要求"],
            "课件": ["课件", "PPT", "幻灯片", "演示文稿", "课件资源"],
            "课例": ["课例", "教学视频", "课堂实录", "视频", "教学案例", "课堂案例", "讲解", "示范课", "公开课", "观摩课"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "几何画板"],
            "习题": ["习题", "题目", "练习题", "练习", "试题", "测试题", "计算题", "应用题", "填空题", "选择题", "解答题", "证明题", "分层练习", "简单练习", "专项练习", "综合题", "拓展题"],
            "资料": ["资料", "资源", "教学资源", "教学资料", "参考资料"]
        }
        
        for resource_type, keywords in resource_type_keywords.items():
            if any(kw in query for kw in keywords):
                resource_types.append(resource_type)
        
        # 确保至少返回一个资源类型
        if not resource_types:
            resource_types.append("资料")
        
        return list(set(resource_types))
    
    def _extract_question_type(self, query: str) -> str:
        """
        V45.0改进：从查询中提取题目类型
        
        Args:
            query: 用户查询
        
        Returns:
            题目类型字符串
        """
        # 使用新的多维度提取方法
        conditions = self._extract_query_conditions(query)
        return conditions['question_type']
    
    def _deduplicate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        对检索结果进行去重
        
        Args:
            results: 检索结果
        
        Returns:
            去重后的结果
        """
        deduplicated = {
            "documents": [[]],
            "metadatas": [[]],
            "distances": [[]],
            "ids": [[]]
        }
        
        seen_questions = set()
        
        print(f"   📊 开始去重，原始结果数量: {len(results['metadatas'][0])}")
        
        for i, meta in enumerate(results["metadatas"][0]):
            question = meta.get('题干', '') or results["documents"][0][i]
            # 使用题目内容的前150个字符作为去重依据，增加准确性
            question_key = question[:150].strip()
            
            if question_key not in seen_questions:
                seen_questions.add(question_key)
                deduplicated["documents"][0].append(results["documents"][0][i])
                deduplicated["metadatas"][0].append(meta)
                deduplicated["distances"][0].append(results["distances"][0][i])
                deduplicated["ids"][0].append(results["ids"][0][i])
            else:
                print(f"   ⚠️ 去重移除重复题目: {question[:50]}...")
        
        print(f"   📊 去重完成，剩余结果数量: {len(deduplicated['metadatas'][0])}")
        return deduplicated
    
    def _get_summary(self, classified: Dict[str, Any]) -> str:
        """
        生成检索结果摘要
        
        Args:
            classified: 分类后的资源
        
        Returns:
            摘要字符串
        """
        summary_parts = []
        
        if classified["theory_resources"]:
            summary_parts.append(f"理论{len(classified['theory_resources'])}条")
        if classified["lesson_plan_patterns"]:
            summary_parts.append(f"教案{len(classified['lesson_plan_patterns'])}条")
        if classified["exercise_resources"]:
            summary_parts.append(f"习题{len(classified['exercise_resources'])}条")
        if classified["visualization_examples"]:
            summary_parts.append(f"可视化{len(classified['visualization_examples'])}条")
        if classified["courseware_resources"]:
            summary_parts.append(f"课件{len(classified['courseware_resources'])}条")
        if classified["lesson_case_resources"]:
            summary_parts.append(f"课例{len(classified['lesson_case_resources'])}条")
        if classified["ggb_resources"]:
            summary_parts.append(f"GGB{len(classified['ggb_resources'])}条")
        if classified["syllabus_resources"]:
            summary_parts.append(f"教学大纲{len(classified['syllabus_resources'])}条")
        
        return ", ".join(summary_parts) if summary_parts else "无结果"
    
    def _extract_core_theme(self, query: str) -> str:
        """
        提取核心主题（使用LLM动态提取，支持完整主题识别，支持多个主题）
        
        Args:
            query: 用户查询
            
        Returns:
            核心主题字符串（多个主题用逗号分隔）
        """
        print(f"🔍 开始提取核心主题，查询: '{query}'")
        
        # 1. 直接提取查询意图（避免调用_extract_query_conditions导致递归）
        intent = ''
        intent_patterns = [
            ('练习', ['练习题', '习题', '题目', '测试题', '题']),
            ('学习', ['学习', '了解', '掌握', '理解', '认识']),
            ('教学', ['教学', '教案', '课件', '教学设计', '教学方案']),
            ('复习', ['复习', '巩固', '回顾', '总结']),
            ('备考', ['备考', '冲刺', '模拟', '真题']),
            ('比较', ['比较', '对比', '区别', '联系', '异同']),
            ('应用', ['应用', '实际应用', '应用题', '实践'])
        ]
        for intent_name, patterns in intent_patterns:
            for pattern in patterns:
                if pattern in query:
                    intent = intent_name
                    break
            if intent:
                break
        
        # 2. 首先检查查询中是否包含资源类型词
        resource_type_keywords = [
            "教案", "教学设计", "教学方案", "教学大纲", "大纲", "课程标准",
            "课件", "PPT", "幻灯片", "课例", "教学视频", "课堂实录",
            "GGB", "GeoGebra", "动态图", "可视化", "习题", "题目", "练习题",
            "测试题", "计算题", "应用题", "填空题", "选择题", "解答题", "证明题"
        ]
        
        # 检查查询是否包含资源类型词
        has_resource_type = any(keyword in query for keyword in resource_type_keywords)
        
        # 3. 移除资源类型词和修饰词
        cleaned_query = query
        # 移除资源类型词
        for keyword in resource_type_keywords:
            cleaned_query = cleaned_query.replace(keyword, "").strip()
        # 移除修饰词
        modifier_words = [
            "基础", "简单", "中等", "难", "困难", "拔高", "刚学", "入门", "初级",
            "一般", "普通", "常见", "挑战", "压轴", "适中", "容易", "提高", "进阶", "综合",
            "高一", "高二", "高三", "初中", "初一", "初二", "初三",
            "几道", "一些", "几个", "少量", "多个",
            "学习", "了解", "掌握", "理解", "认识", "复习", "巩固", "回顾", "总结",
            "备考", "冲刺", "模拟", "真题", "比较", "对比", "区别", "联系", "异同",
            "应用", "实际应用", "实践"
        ]
        for word in modifier_words:
            cleaned_query = cleaned_query.replace(word, "").strip()
        
        if cleaned_query != query:
            print(f"   📝 清理后的查询: '{cleaned_query}'")
        
        # 4. 首先使用关键词匹配提取主题
        print("🔑 首先使用关键词匹配提取主题...")
        # 特殊处理：三角恒等变换、导数、指数函数和对数函数对比等主题
        if "三角恒等变换" in query:
            keyword_theme = "三角恒等变换"
        elif "导数" in query:
            keyword_theme = "导数"
        elif any(phrase in query for phrase in ["指数函数和对数函数对比", "指数和对数对比", "指数对数对比"]):
            keyword_theme = "指数函数,对数函数"
        else:
            keyword_theme = self._extract_theme_with_keywords(cleaned_query)
        print(f"✅ 关键词匹配结果: '{keyword_theme}'")
        
        # 5. 基于查询意图调整主题提取策略
        if intent == '比较':
            # 对于比较类查询，尝试提取多个主题
            print("   📝 比较类查询，尝试提取多个主题")
            # 检查是否包含比较关键词
            comparison_words = ["比较", "对比", "区别", "联系", "异同"]
            if any(word in query for word in comparison_words):
                # 尝试从查询中提取两个主题
                # 改进：增强对比类查询的主题提取
                print("   📝 增强对比类查询的主题提取...")
                # 分割查询，提取两个主题
                parts = query.split('和')
                if len(parts) == 2:
                    theme1 = self._extract_theme_with_keywords(parts[0].strip())
                    theme2 = self._extract_theme_with_keywords(parts[1].strip())
                    if theme1 and theme2:
                        keyword_theme = f"{theme1},{theme2}"
                        print(f"   ✅ 提取到对比主题: {keyword_theme}")
                # 处理其他分割词
                elif '与' in query:
                    parts = query.split('与')
                    if len(parts) == 2:
                        theme1 = self._extract_theme_with_keywords(parts[0].strip())
                        theme2 = self._extract_theme_with_keywords(parts[1].strip())
                        if theme1 and theme2:
                            keyword_theme = f"{theme1},{theme2}"
                            print(f"   ✅ 提取到对比主题: {keyword_theme}")
        
        # 6. 如果关键词匹配成功提取到具体主题，直接使用
        # V65.0改进：当查询包含资源类型词时，允许提取"函数"这样的通用主题
        if keyword_theme and (keyword_theme not in ["函数", "数学", "教学"] or has_resource_type or intent):
            print("✅ 使用关键词匹配结果作为核心主题")
            return keyword_theme
        
        # 7. V72.0改进：如果查询包含资源类型词，且关键词匹配失败，尝试从原始查询中提取主题
        if has_resource_type and not keyword_theme:
            print("   📝 V72.0改进：查询包含资源类型词，尝试从原始查询中提取主题")
            keyword_theme = self._extract_theme_with_keywords(query)
            print(f"   ✅ 从原始查询提取的主题: '{keyword_theme}'")
            if keyword_theme:
                print("✅ 使用从原始查询提取的主题作为核心主题")
                return keyword_theme
        
        # 8. 备用方案：使用LLM动态提取主题
        try:
            print("🤖 尝试使用LLM提取主题...")
            llm_theme = self._extract_theme_with_llm(cleaned_query, has_resource_type, intent)
            if llm_theme:
                print(f"✅ LLM提取的主题: '{llm_theme}'")
                return llm_theme
            else:
                print("⚠️ LLM返回空结果")
        except Exception as e:
            print(f"❌ LLM主题提取失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 9. 如果LLM也失败，使用关键词匹配结果
        print("✅ 使用关键词匹配结果作为核心主题")
        return keyword_theme
    
    def _extract_theme_with_llm(self, query: str, has_resource_type: bool = False, intent: str = "") -> str:
        """
        使用LLM动态提取主题
        
        Args:
            query: 用户查询
            has_resource_type: 查询是否包含资源类型词
            intent: 查询意图
            
        Returns:
            提取的主题字符串
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # 构建提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""你是一个高中数学主题识别专家。你的任务是从用户查询中提取核心数学主题。

规则：
1. 提取最具体、最细分的主题（例如："函数的单调性"比"函数"更具体）
2. 如果查询包含多个主题，用逗号分隔
3. 只返回主题名称，不要解释，不要添加任何其他文字
4. 主题应该简洁明了，通常格式为"XXX的YYY"（如"函数的单调性"、"三角函数的图像"等）
5. 必须返回一个有效的主题，不能返回空字符串
6. 重要：不要提取过于宽泛的主题，如单独的"函数"、"数学"等，除非查询包含资源类型词（如"选择题"、"习题"等）或有明确的查询意图
7. 重要：具体函数类型（如"三角函数"、"幂函数"、"对数函数"、"指数函数"）是有效主题
8. 重要：如果查询包含资源类型词（如"选择题"、"习题"、"题目"等）且只提到"函数"，可以提取"函数"作为通用主题
9. 重要：忽略查询中的修饰词，如"基础一点的"、"中等难度的"、"高二的"、"难一点的"等，只提取核心数学主题
10. 重要：动态识别语义相关的概念，将其映射到核心主题。思考过程如下：
   - 分析查询中的关键词和概念
   - 忽略修饰词和无关词汇
11. 重要：对于比较类查询（意图为"比较"），尝试提取多个相关主题，用逗号分隔
   - 判断这些概念与哪些数学主题相关
   - 将相关概念映射到最具体的核心主题
   - 例如："抛物线"与二次函数的图像相关，应映射到"二次函数"
   - 例如："放射性衰变"是指数变化的实例，应映射到"指数函数"
   - 例如："周期性变化"是三角函数的特征，应映射到"三角函数"
   - 例如："图像对称性"与函数的奇偶性相关，应映射到"函数的奇偶性"
   - 例如："方程求解"与函数的零点相关，应映射到"函数的零点"
   - 例如："实际应用"与函数的应用相关，应映射到"函数的应用"
11. 重要：对于"对比"、"比较"、"和"、"与"等表示多个主题的查询，必须提取所有相关主题
12. 重要：对于"指数对数对比"、"指数和对数"等查询，应提取"指数函数,对数函数"

有效主题示例：
-- "函数的单调性"、"函数的奇偶性"、"函数的周期性"
-- "二次函数"、"三角函数"、"幂函数"、"对数函数"、"指数函数"
-- "对数函数运算"、"指数与对数函数综合"
-- "诱导公式"、"三角恒等变换"
-- "函数的概念"、"函数的性质"
-- "对数函数的应用"、"指数函数的应用"、"函数的应用"
-- "函数"（当查询包含资源类型词如"选择题"、"习题"时）

无效主题（不要提取）：
- 单独的"函数"（过于宽泛，除非查询包含资源类型词）
- 单独的"数学"（过于宽泛）
- 修饰词如"基础"、"中等"、"难"、"高二"等

示例：
- 输入："关于函数单调性的教案" -> 输出："函数的单调性"
- 输入："给我找一些三角函数诱导公式的习题" -> 输出："诱导公式"
- 输入："指数函数和对数函数的教案" -> 输出："指数函数,对数函数"
- 输入："函数的奇偶性和周期性" -> 输出："函数的奇偶性,函数的周期性"
- 输入："关于二次函数图像和性质的教学资源" -> 输出："二次函数的图像和性质"
- 输入："关于函数单调性的教案" -> 输出："函数的单调性"
- 输入："单调性教案" -> 输出："函数的单调性"
- 输入："帮我找一下三角函数、幂函数和对数函数的教案资源" -> 输出："三角函数,幂函数,对数函数"
- 输入："二次函数和指数函数的计算题" -> 输出："二次函数,指数函数"
- 输入："给我找一些二次函数的基础习题" -> 输出："二次函数"
- 输入："推荐一些对数函数的应用题" -> 输出："对数函数的应用"
- 输入："找一些指数函数的实际应用" -> 输出："指数函数的应用"
- 输入："二次函数的图像和性质" -> 输出："二次函数的图像和性质"
- 输入："关于二次函数的教学资源" -> 输出："二次函数"
- 输入："基础一点的二次函数选择题" -> 输出："二次函数"
- 输入："高二的三角函数习题" -> 输出："三角函数"
- 输入："中等难度的指数函数题" -> 输出："指数函数"
- 输入："函数单调性的证明题" -> 输出："函数的单调性"
- 输入："想要一些三角函数的解答题" -> 输出："三角函数"
- 输入："指数对数对比题" -> 输出："指数函数,对数函数"
- 输入："指数和对数的对比" -> 输出："指数函数,对数函数"
- 输入："二次函数和指数函数对比" -> 输出："二次函数,指数函数"

附加信息：原始查询{"包含" if has_resource_type else "不包含"}资源类型词，因此{"可以" if has_resource_type else "不可以"}提取通用主题如"函数"作为核心主题。"""),
            ("user", "用户查询：{query}\n\n请提取核心主题（只输出主题名称）：")
        ])
        
        # 获取模型
        model = self.model_config.get_model("intent")
        
        # 构建链
        chain = prompt | model | StrOutputParser()
        
        # 调用模型
        result = chain.invoke({"query": query})
        
        # 清理结果
        result = result.strip()
        print(f"🤖 LLM原始输出: '{result}'")
        
        if result and len(result) > 0:
            # 检查结果是否包含主题相关词汇（扩展验证关键词列表）
            theme_keywords = [
                "单调性", "奇偶性", "周期性", "对称性", "概念", "性质", "应用", "图像", 
                "诱导公式", "恒等变换", "零点", "二分法",
                "函数", "指数", "对数", "三角", "幂", "二次",
                "抛物线", "方程", "周期性变化", "实际应用",
                "对数函数的应用", "指数函数的应用", "函数的应用",
                "对数函数运算", "指数与对数函数综合", "换底公式"
            ]
            if any(keyword in result for keyword in theme_keywords):
                return result
            else:
                print(f"⚠️ LLM输出不包含主题关键词: '{result}'，使用关键词匹配")
        
        print(f"⚠️ LLM返回空或无效结果，使用关键词匹配")
        return ""
    
    def _extract_theme_with_keywords(self, query: str) -> str:
        """
        使用关键词匹配提取主题（备用方案）- 改进版
        支持连接词分割和多主题提取
        
        Args:
            query: 用户查询
            
        Returns:
            核心主题字符串（多个主题用逗号分隔）
        """
        # 收集所有匹配的主题
        matched_themes = []
        
        # V53.3改进：动态获取完整主题列表，从knowledge_hierarchy中提取
        # 不再硬编码具体主题，使系统能够自动适应资源库扩展
        complete_themes = self.all_themes
        
        # 打印完整主题列表，方便调试
        print(f"   📋 完整主题列表: {complete_themes}")
        
        print(f"🔑 关键词匹配 - 查询: '{query}'")
        
        # 改进1：使用连接词分割查询，分别提取每个部分的主题
        # 定义连接词列表
        conjunctions = ['和', '与', '及', '、', '以及', '还有', '跟', '同']
        
        # 分割查询为多个子查询
        sub_queries = [query]
        
        # 对每个连接词进行分割
        for conj in conjunctions:
            temp_sub_queries = []
            for sq in sub_queries:
                if conj in sq:
                    parts = sq.split(conj)
                    temp_sub_queries.extend([p.strip() for p in parts if p.strip()])
                else:
                    temp_sub_queries.append(sq)
            sub_queries = temp_sub_queries
        
        # 去重并保持顺序
        seen = set()
        unique_sub_queries = []
        for sq in sub_queries:
            if sq not in seen:
                seen.add(sq)
                unique_sub_queries.append(sq)
        sub_queries = unique_sub_queries
        
        if len(sub_queries) > 1:
            print(f"   🔄 检测到连接词，将查询分割为 {len(sub_queries)} 个子查询: {sub_queries}")
        
        # 对每个子查询分别提取主题
        for sub_query in sub_queries:
            # 优先匹配完整主题（支持去掉"的"字的匹配）
            query_without_de = sub_query.replace("的", "")
            
            # 特殊处理：如果子查询是函数性质关键词，自动添加"函数的"前缀
            function_property_keywords = ["单调性", "奇偶性", "周期性", "对称性", "零点", "定义域", "值域", "性质"]
            for prop in function_property_keywords:
                if prop in sub_query:
                    enhanced_sub_query = f"函数的{prop}"
                    print(f"   📝 增强子查询: '{sub_query}' -> '{enhanced_sub_query}'")
                    sub_query = enhanced_sub_query
                    query_without_de = sub_query.replace("的", "")
                    break
            
            # V53.3改进：不再硬编码三角函数主题，让所有主题都按顺序匹配
            # 直接匹配所有完整主题（支持去掉"的"字的匹配）
            for theme in complete_themes:
                # 去掉"的"字进行比较
                theme_without_de = theme.replace("的", "")
                
                # 检查完整匹配或关键词匹配
                if (theme in sub_query or 
                    theme_without_de in query_without_de or
                    any(keyword in sub_query for keyword in self.knowledge_hierarchy.get(theme, {}).get('keywords', []))):
                    if theme not in matched_themes:
                        print(f"   ✓ 匹配到完整主题: '{theme}' (来自子查询: '{sub_query}')")
                        matched_themes.append(theme)
        
        # 如果没有匹配到完整主题，使用关键词匹配
        if not matched_themes:
            print(f"   ℹ️  没有匹配到完整主题，使用关键词匹配")
            
            # V53.2改进：使用动态生成的主题关键词，而不是硬编码
            # 从 knowledge_hierarchy 中动态构建 theme_keywords
            theme_keywords = {}
            for theme in self.all_themes:
                theme_info = self.knowledge_hierarchy.get(theme, {})
                keywords = theme_info.get('keywords', [])
                if keywords:
                    theme_keywords[theme] = keywords
            
            # V53.2改进：使用所有主题作为优先级顺序
            priority_order = self.all_themes
            
            for sub_query in sub_queries:
                for theme in priority_order:
                    for keyword in theme_keywords.get(theme, []):
                        if keyword in sub_query and theme not in matched_themes:
                            print(f"   ✓ 匹配到关键词: '{keyword}' -> 主题: '{theme}'")
                            matched_themes.append(theme)
        

        
        # V53.2改进：动态识别应用场景
        # 检查是否包含应用场景关键词
        application_keywords = ["应用", "实际", "问题", "案例", "场景", "生活", "建模", "实际应用", "应用问题", "实际场景"]
        has_application = any(keyword in query for keyword in application_keywords)
        
        # V53.2改进：动态识别包含"应用"的主题，而不是硬编码
        if has_application:
            # 找到所有包含"应用"的主题
            app_themes = [theme for theme in self.all_themes if "应用" in theme]
            
            # 检查是否已经匹配到基础主题，如果是，添加对应的应用主题
            for app_theme in app_themes:
                # 尝试从应用主题中提取基础主题（去掉"的应用"或"应用"）
                base_theme = app_theme.replace("的应用", "").replace("应用", "").strip()
                if base_theme and base_theme in matched_themes and app_theme not in matched_themes:
                    print(f"   📝 增强应用场景识别：添加'{app_theme}'主题")
                    matched_themes.append(app_theme)
        
        # 动态语义关联检测：如果仍然没有匹配到主题，尝试使用向量相似度查找相关资源
        if not matched_themes:
            print(f"   🔍 尝试动态语义关联检测...")
            # 提取查询的核心概念（去除常见词）
            query_clean = query.replace("帮我找", "").replace("教案", "").replace("的", "").replace("一下", "").strip()
            if query_clean:
                # 特殊处理：如果查询包含"图像"，尝试匹配函数相关主题
                if "图像" in query_clean:
                    print(f"   📝 检测到'图像'关键词，尝试匹配函数相关主题")
                    # 遍历所有函数相关主题
                    for theme in self.all_themes:
                        if "函数" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"图像"但还没有匹配到主题，尝试匹配三角函数相关主题
                if not matched_themes and "图像" in query_clean:
                    print(f"   📝 尝试匹配三角函数相关主题")
                    for theme in self.all_themes:
                        if "三角" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加三角函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"函数"，尝试匹配函数相关主题
                if not matched_themes and "函数" in query_clean:
                    print(f"   📝 检测到'函数'关键词，尝试匹配函数相关主题")
                    for theme in self.all_themes:
                        if "函数" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数相关主题: '{theme}'")
                            break
                # 特殊处理：如果查询包含"概念"，尝试匹配函数概念主题
                if not matched_themes and "概念" in query_clean:
                    print(f"   📝 检测到'概念'关键词，尝试匹配函数概念主题")
                    for theme in self.all_themes:
                        if "函数的概念" in theme:
                            matched_themes.append(theme)
                            print(f"   ✓ 添加函数概念主题: '{theme}'")
                            break
                # 如果仍然没有匹配到主题，使用查询本身作为主题
                if not matched_themes:
                    print(f"   📝 使用查询本身作为主题: '{query_clean}'")
                    matched_themes.append(query_clean)
        
        # V53.1改进：通用主题处理，不再硬编码具体主题
        # 如果没有匹配到任何具体主题，但查询包含主题关键词和资源类型词，返回相应的通用主题
        if not matched_themes:
            # 检查是否是资源请求
            resource_request_patterns = ["来几道", "来一些", "给我", "找", "推荐", "有没有", "要几道"]
            is_resource_request = any(pattern in query for pattern in resource_request_patterns)
            
            # 检查是否包含资源类型词
            resource_type_keywords = ["选择题", "习题", "题目", "练习题", "测试题", "教案", "课件", "GGB", "教学大纲", "课例"]
            has_resource_type = any(keyword in query for keyword in resource_type_keywords)
            
            # V53.1改进：使用动态生成的主题关键词，而不是硬编码
            # 检查查询中是否包含任何主题关键词
            for theme in self.all_themes:
                theme_keywords = self.knowledge_hierarchy.get(theme, {}).get('keywords', [])
                if any(kw in query for kw in theme_keywords):
                    # 如果是资源请求或包含资源类型词，添加该主题
                    if is_resource_request or has_resource_type:
                        print(f"   📝 通用主题处理：添加'{theme}'主题")
                        matched_themes.append(theme)
                    break
            
            # V61.0改进：如果仍然没有匹配到主题，添加默认主题"函数"
            if not matched_themes:
                print(f"   📝 默认主题处理：添加'函数'主题")
                matched_themes.append("函数")
        
        result = ",".join(matched_themes) if matched_themes else "函数"
        print(f"   ✅ 关键词匹配结果: '{result}'")
        return result
    
    def get_theory_resources(self) -> List[Dict[str, Any]]:
        """
        获取所有理论资源（用于教案生成）
        
        Returns:
            理论资源列表
        """
        try:
            # 获取客户端
            client = self.vector_db_builder.get_chroma_client()
            collection = client.get_collection(name=self.COLLECTION_NAME)
            
            # 查询所有理论资源
            results = collection.get(
                where={"resource_type": "theory"},
                include=["documents", "metadatas"]
            )
            
            theory_resources = []
            
            for i, doc in enumerate(results["documents"]):
                metadata = results["metadatas"][i]
                
                resource = {
                    "title": metadata.get('title', ''),
                    "content": doc,
                    "source": metadata.get('source_file', ''),
                    "metadata": metadata
                }
                
                theory_resources.append(resource)
            
            return theory_resources
            
        except Exception as e:
            print(f"❌ 获取理论资源失败: {str(e)}")
            return []


# 向后兼容的函数接口
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
        "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示", "演示"],
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
        print(f"📋 V53.12识别到资源类型: {resource_types}")
    
    return retriever.retrieve(query, intent, resource_types=resource_types if resource_types else None)