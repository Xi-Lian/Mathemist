"""
资源检索模块

职责：
- 使用ChromaDB进行语义检索
- 根据查询和意图检索相关资源
- 对检索结果进行分类和组织
- 实现习题资源的特殊处理逻辑

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
from typing import Dict, Any, List
from .model_config import model_config
from .resource_classifier import ResourceClassifier
from .vector_database_builder import VectorDatabaseBuilder
from .resource_table_parser import ResourceTableParser
from .theme_matcher import get_theme_matcher
from ..config.resource_type_config import (
    get_db_type,
    get_resource_type_mapping,
    get_standard_name,
    get_all_user_types,
    get_all_db_types
)


class ResourceRetriever:
    """资源检索器"""
    
    COLLECTION_NAME = "math_resources"
    DEFAULT_N_RESULTS = 200
    
    def __init__(self, learning_resource_path: str = None):
        """
        初始化资源检索器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
        """
        self.model_config = model_config
        
        # 设置learning_resource路径
        if learning_resource_path is None:
            # 默认路径：backend/../learning_resource
            current_dir = Path(__file__).parent.parent.parent
            learning_resource_path = current_dir / 'learning_resource'
        
        # 确保learning_resource_path是绝对路径
        self.learning_resource_path = Path(learning_resource_path).resolve()
        
        # 初始化向量数据库构建器和解析器
        self.vector_db_builder = VectorDatabaseBuilder(str(self.learning_resource_path))
        self.parser = ResourceTableParser(str(self.learning_resource_path))
    
    def retrieve(self, query: str, intent: str = "search", n_results: int = None, resource_types: List[str] = None) -> Dict[str, Any]:
        """
        根据查询和意图检索相关资源
        
        Args:
            query: 用户查询
            intent: 用户意图
            n_results: 返回结果数量，默认为50
            resource_types: 用户明确提到的资源类型列表（用于精准检索）
        
        Returns:
            检索结果字典，包含各类资源
        """
        try:
            print(f" 资源检索开始")
            print(f"📝 查询: {query}")
            print(f"🎯 意图: {intent}")
            print(f"📋 资源类型: {resource_types}")
            
            # 检查向量数据库是否存在
            if not self._check_vector_db_exists():
                print("⚠️  向量数据库不存在，尝试构建...")
                if not self.vector_db_builder.build_vector_database():
                    print("❌ 向量数据库构建失败")
                    return self._get_empty_result()
            
            # 获取客户端和模型
            client = self.vector_db_builder.get_chroma_client()
            embedding_model = self.vector_db_builder.get_embedding_model()
            
            # 获取集合
            collection = client.get_collection(name=self.COLLECTION_NAME)
            
            # 生成查询向量
            query_embedding = self._generate_query_embedding(query, embedding_model)
            
            # 提取核心主题（支持完整主题识别）
            core_theme = self._extract_core_theme(query)
            print(f"🧠 识别核心主题: {core_theme}")
            
            # 执行查询
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results or self.DEFAULT_N_RESULTS,
                include=["documents", "metadatas", "distances"]
            )
            
            # 打印查询结果的基本信息
            if results.get("documents") and results["documents"][0]:
                print(f"📊 查询返回 {len(results['documents'][0])} 条结果")
                # 检查是否包含幂函数相关资源
                power_function_count = 0
                for i, metadata in enumerate(results.get("metadatas", [[]])[0]):
                    source_file = metadata.get('source_file', '')
                    if '幂函数' in source_file or '3-3' in source_file:
                        power_function_count += 1
                        distance = results.get("distances", [[]])[0][i]
                        relevance = 1 - distance
                        print(f"   🎯 找到幂函数资源: {source_file}, 距离: {distance:.3f}, 相似度: {relevance:.1%}")
                print(f"   幂函数相关资源数量: {power_function_count}")
                
                # 处理检索结果
                classified_resources = self._classify_results(results, resource_types, core_theme)
                
                # 所有资源类型按相似度和主题匹配度降序排序（通用化）
                for category in classified_resources:
                    if classified_resources[category] and core_theme:
                        print(f"\n🔍 {category}资源排序（核心主题: {core_theme}）...")
                        # 排序规则：主题匹配优先，然后按相似度
                        classified_resources[category].sort(
                            key=lambda x: (
                                -x.get('theme_match', False),  # 主题匹配优先
                                -x.get('relevance', 0)         # 然后按相似度
                            )
                        )
                        print(f"   ✅ {category}资源排序完成，主题匹配优先，然后按相似度降序排列")
                
                print(f"✅ 检索完成: {self._get_summary(classified_resources)}")
                
                return classified_resources
            
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
    
    def _classify_results(self, results: Dict[str, Any], resource_types: List[str] = None, core_theme: str = "") -> Dict[str, Any]:
        """
        对检索结果进行分类
        
        Args:
            results: ChromaDB查询结果
            resource_types: 用户明确提到的资源类型列表（用于精准检索）
            core_theme: 核心主题
        
        Returns:
            分类后的资源字典
        """
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
                
                # 如果用户明确指定了资源类型，只保留匹配的类型
                # 特殊处理：如果用户指定了"资料"或"资源"，则保留所有资源
                if resource_types and not any(rt in ["资料", "资源"] for rt in resource_types):
                    print(f"\n🔍 资源类型过滤 - 用户指定类型: {resource_types}")
                    
                    # 使用统一的资源类型映射
                    matched = False
                    for user_type in resource_types:
                        # 获取映射后的数据库类型
                        mapped_db_type = get_db_type(user_type)
                        
                        if mapped_db_type:
                            if resource_type == mapped_db_type:
                                matched = True
                                print(f"   ✓ 用户类型 '{user_type}' 映射为 '{mapped_db_type}'，匹配当前资源类型")
                                break
                        else:
                            # 如果找不到映射，尝试用原始词进行模糊匹配
                            print(f"   ⚠️ 未知的资源类型: '{user_type}'，尝试模糊匹配...")
                            if user_type.lower() in resource_type.lower():
                                matched = True
                                print(f"   ✓ 模糊匹配成功: '{user_type}' ≈ '{resource_type}'")
                                break
                    
                    # 如果不匹配，跳过这个资源
                    if not matched:
                        print(f"   ✗ 跳过资源: 类型 '{resource_type}' 不匹配")
                        continue
                
                # 创建资源对象
                resource = self._create_resource(doc, metadata, distance, resource_type, core_theme)
                
                # 分类资源
                self._add_to_category(classified, resource_type, resource)
        
        return classified
    
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
    
    def _create_resource(self, doc: str, metadata: Dict[str, Any], distance: float, resource_type: str, core_theme: str = "") -> Dict[str, Any]:
        """
        创建资源对象（带主题匹配）
        
        Args:
            doc: 文档内容
            metadata: 元数据
            distance: 距离
            resource_type: 资源类型
            core_theme: 核心主题
        
        Returns:
            资源字典
        """
        # 基本资源信息 - 保留原始相似度作为基础分！
        base_relevance = 1 - distance
        resource = {
            "title": metadata.get('title', '未知'),
            "content": doc,
            "source": metadata.get('source_file', ''),
            "relevance": base_relevance,
            "metadata": metadata,
            "base_relevance": base_relevance,
            "theme_match": False,
            "conflict_theme": False
        }
        
        # 使用主题匹配器进行主题匹配
        if core_theme:
            from .theme_matcher import get_theme_matcher
            theme_matcher = get_theme_matcher()
            
            # 支持多个核心主题（用逗号分隔）
            core_themes = [t.strip() for t in core_theme.split(",") if t.strip()]
            
            # 对每个核心主题进行匹配，取最高的加分
            max_relevance_boost = 0.0
            max_conflict_penalty = 0.0
            is_theme_match = False
            is_conflict_theme = False
            
            for theme in core_themes:
                match_result = theme_matcher.match_theme(
                    core_theme=theme,
                    metadata=metadata,
                    document=doc,
                    verbose=False  # 不输出详细日志，避免过多输出
                )
                
                # 记录最高的加分
                if match_result["is_theme_match"] and match_result["relevance_boost"] > max_relevance_boost:
                    max_relevance_boost = match_result["relevance_boost"]
                    is_theme_match = True
                
                # 记录最高的冲突减分
                if match_result["is_conflict_theme"] and match_result["relevance_penalty"] > max_conflict_penalty:
                    max_conflict_penalty = match_result["relevance_penalty"]
                    is_conflict_theme = True
            
            # 保留基础分，只在基础分上加减！
            final_relevance = base_relevance
            
            # 应用主题匹配加分
            if is_theme_match:
                final_relevance += max_relevance_boost
                resource["theme_match"] = True
                resource["theme_boost"] = max_relevance_boost
            
            # 应用冲突主题减分（但不低于基础分的50%，保留最低相关性）
            if is_conflict_theme:
                final_relevance -= max_conflict_penalty
                resource["conflict_theme"] = True
                resource["conflict_penalty"] = max_conflict_penalty
                # 确保不低于基础分的50%，避免完全消失
                final_relevance = max(base_relevance * 0.5, final_relevance)
            
            # 设置最终相似度，确保在0到1之间
            final_relevance = max(0.0, min(1.0, final_relevance))
            resource["relevance"] = final_relevance
            
            # 输出分数变化（只输出第一个主题的详细信息）
            first_theme = core_themes[0] if core_themes else ""
            if first_theme:
                match_result = theme_matcher.match_theme(
                    core_theme=first_theme,
                    metadata=metadata,
                    document=doc,
                    verbose=True
                )
                print(f"   📊 基础分: {base_relevance:.1%}")
                if is_theme_match:
                    print(f"   ➕ 主题匹配加分: +{max_relevance_boost:.1%} (主题: {core_themes})")
                if is_conflict_theme:
                    print(f"   ➖ 冲突主题减分: -{max_conflict_penalty:.1%}")
                print(f"   🎯 最终相似度: {final_relevance:.1%} (基础分: {base_relevance:.1%})")
        
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
        
        return resource
    
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
        
        if filename:
            # 有文件名，说明是图片题目
            resource['title'] = f"习题（图片）: {filename}"
            resource['content'] = f"题目类型：{metadata.get('题目类型', '')}\n题目描述：{metadata.get('题干', '')}\n知识点：{metadata.get('知识点标签', '')}\n难度：{metadata.get('难度（1-5）', '')}"
            resource['is_image_exercise'] = True
            resource['filename'] = filename
            resource['source'] = source_file
        else:
            # 文字题目，显示完整题目
            question = metadata.get('题干', '')
            answer = metadata.get('解析', '')
            
            resource['title'] = f"习题: {metadata.get('题目类型', '')}"
            resource['content'] = f"题目：{question}\n\n解析：{answer}"
            resource['is_image_exercise'] = False
            resource['source'] = source_file
    
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
        
        resource['title'] = f"教案: {title}"
        resource['content'] = content
    
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
        classified[category].append(resource)
    
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
            "syllabus_resources": []
        }
    
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
        提取核心主题（支持完整主题识别，支持多个主题）
        
        Args:
            query: 用户查询
            
        Returns:
            核心主题字符串（多个主题用逗号分隔）
        """
        # 完整主题定义（按长度降序排序，优先匹配更长的主题）
        complete_themes = [
            # 函数相关主题
            "函数的概念", "函数的表示法", "函数的性质", "函数的应用",
            "指数函数的概念", "指数函数的图像和性质", "指数函数的应用",
            "对数函数的概念", "对数函数的图像和性质", "对数函数的应用",
            "三角函数的概念", "三角函数的图像与性质", "三角函数的应用",
            "幂函数的图像和性质", "幂函数的应用",
            "二次函数的图像和性质", "二次函数的应用",
            "诱导公式", "三角恒等变换", "函数的零点", "二分法",
            "任意角", "弧度制", "同角三角函数的基本关系", "函数模型的应用",
            
            # 基础主题
            "指数函数", "对数函数", "三角函数", "幂函数", "二次函数",
            "一次函数", "分段函数", "函数"
        ]
        
        # 收集所有匹配的主题
        matched_themes = []
        
        # 优先匹配完整主题
        for theme in complete_themes:
            if theme in query and theme not in matched_themes:
                matched_themes.append(theme)
        
        # 如果没有匹配到完整主题，使用关键词匹配
        if not matched_themes:
            # 备用：关键词匹配
            theme_keywords = {
                "函数的概念": ["函数概念", "函数的定义", "什么是函数", "函数的意义"],
                "函数的应用": ["函数应用", "函数的应用", "应用", "建模", "实际问题", "数学建模"],
                "指数函数": ["指数函数", "指数与指数函数", "2^x", "a^x", "e^", "指数增长", "指数衰减"],
                "对数函数": ["对数函数", "对数与对数函数", "log", "ln", "对数增长", "对数衰减"],
                "三角函数": ["三角函数", "三角", "sin", "cos", "tan", "正弦", "余弦", "正切"],
                "二次函数": ["二次函数", "x²", "x^2", "一元二次", "抛物线", "顶点式", "一般式"],
                "幂函数": ["幂函数", "x^a", "x的幂", "幂运算"]
            }
            
            # 按优先级排序
            priority_order = ["函数的概念", "函数的应用", "指数函数", "对数函数", "三角函数", "二次函数", "幂函数"]
            
            for theme in priority_order:
                for keyword in theme_keywords.get(theme, []):
                    if keyword in query and theme not in matched_themes:
                        matched_themes.append(theme)
                        break
        
        # 返回匹配的主题（多个主题用逗号分隔）
        return ",".join(matched_themes) if matched_themes else ""
    
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
    return retriever.retrieve(query, intent)