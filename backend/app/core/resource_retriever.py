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


class ResourceRetriever:
    """资源检索器"""
    
    COLLECTION_NAME = "math_resources"
    DEFAULT_N_RESULTS = 50
    
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
    
    def retrieve(self, query: str, intent: str = "search", n_results: int = None) -> Dict[str, Any]:
        """
        根据查询和意图检索相关资源
        
        Args:
            query: 用户查询
            intent: 用户意图
            n_results: 返回结果数量，默认为20
        
        Returns:
            检索结果字典，包含各类资源
        """
        try:
            print(f"🔍 资源检索开始")
            print(f"📝 查询: {query}")
            print(f"🎯 意图: {intent}")
            
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
            
            # 执行查询
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=n_results or self.DEFAULT_N_RESULTS,
                include=["documents", "metadatas", "distances"]
            )
            
            # 处理检索结果
            classified_resources = self._classify_results(results)
            
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
    
    def _classify_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        对检索结果进行分类
        
        Args:
            results: ChromaDB查询结果
        
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
                
                # 创建资源对象
                resource = self._create_resource(doc, metadata, distance, resource_type)
                
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
    
    def _create_resource(self, doc: str, metadata: Dict[str, Any], distance: float, resource_type: str) -> Dict[str, Any]:
        """
        创建资源对象
        
        Args:
            doc: 文档内容
            metadata: 元数据
            distance: 距离
            resource_type: 资源类型
        
        Returns:
            资源字典
        """
        # 基本资源信息
        resource = {
            "title": metadata.get('title', '未知'),
            "content": doc,
            "source": metadata.get('source_file', ''),
            "relevance": 1 - distance,
            "metadata": metadata
        }
        
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
        
        if filename:
            # 有文件名，说明是图片题目
            resource['title'] = f"习题（图片）: {filename}"
            resource['content'] = f"题目类型：{metadata.get('题目类型', '')}\n题目描述：{metadata.get('题干', '')}\n知识点：{metadata.get('知识点标签', '')}\n难度：{metadata.get('难度（1-5）', '')}"
            resource['is_image_exercise'] = True
            resource['filename'] = filename
        else:
            # 文字题目，显示完整题目
            question = metadata.get('题干', '')
            answer = metadata.get('解析', '')
            
            resource['title'] = f"习题: {metadata.get('题目类型', '')}"
            resource['content'] = f"题目：{question}\n\n解析：{answer}"
            resource['is_image_exercise'] = False
    
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
        
        resource['title'] = f"课例: {chapter}"
        resource['content'] = f"章节：{chapter}\n视频文件名/网址：{filename}\n分析：{analysis}"
        resource['filename'] = filename
    
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