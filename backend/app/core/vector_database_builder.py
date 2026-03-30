"""
向量数据库构建模块
用于基于资源汇总表构建ChromaDB向量数据库
"""

import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

import chromadb
from chromadb.config import Settings

from .resource_table_parser import ResourceTableParser
from .model_config import model_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorDatabaseBuilder:
    """向量数据库构建器"""
    
    def __init__(self, learning_resource_path: str, db_path: str = None):
        """
        初始化向量数据库构建器
        
        Args:
            learning_resource_path: learning_resource文件夹路径
            db_path: 向量数据库存储路径
        """
        # 确保learning_resource_path是绝对路径
        input_path = Path(learning_resource_path).resolve()
        
        # 如果输入路径是learning_resource文件夹本身，使用它
        if input_path.name == 'learning_resource' and input_path.exists():
            self.learning_resource_path = input_path
        else:
            # 从backend/app/core/vector_database_builder.py向上查找项目根目录
            # __file__ = backend/app/core/vector_database_builder.py
            # parent.parent.parent = backend
            # parent.parent.parent.parent = Mathemist
            backend_dir = Path(__file__).parent.parent.parent
            lr_path = backend_dir / 'learning_resource'
            if lr_path.exists():
                self.learning_resource_path = lr_path
            else:
                # 尝试从backend目录的上级目录查找
                project_root = backend_dir.parent
                lr_path = project_root / 'learning_resource'
                if lr_path.exists():
                    self.learning_resource_path = lr_path
                else:
                    # 使用输入路径作为learning_resource路径
                    self.learning_resource_path = input_path
        
        # 使用正确的learning_resource_path初始化ResourceTableParser
        self.parser = ResourceTableParser(str(self.learning_resource_path))
        # 使用全局单例model_config，避免重复创建模型实例
        self.model_config = model_config
        
        # 设置数据库路径
        if db_path is None:
            # 默认路径：backend/chroma_db（与服务实际使用的路径一致）
            current_dir = Path(__file__).parent.parent.parent
            db_path = current_dir / 'chroma_db'
        
        self.db_path = Path(db_path).resolve()
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        # ChromaDB配置
        self.COLLECTION_NAME = "math_resources"
        
    def get_chroma_client(self) -> chromadb.Client:
        """
        获取ChromaDB客户端
        
        Returns:
            ChromaDB客户端
        """
        client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        return client
    
    def get_embedding_model(self):
        """
        获取embedding模型
        
        Returns:
            embedding模型
        """
        return self.model_config.get_embedding_model()
    
    def build_vector_database(self, force_rebuild: bool = False, batch_size: int = 50) -> bool:
        """
        构建向量数据库
        
        Args:
            force_rebuild: 是否强制重建数据库
            batch_size: 分批生成向量和写库的批次大小
            
        Returns:
            是否构建成功
        """
        try:
            # 获取ChromaDB客户端
            client = self.get_chroma_client()
            
            # 检查集合是否存在
            collection_exists = self.COLLECTION_NAME in [col.name for col in client.list_collections()]
            
            if collection_exists and not force_rebuild:
                logger.info(f"向量数据库已存在: {self.db_path}")
                logger.info("如需重新构建，请使用 force_rebuild=True")
                return True
            
            # 如果存在且需要重建，删除旧集合
            if collection_exists and force_rebuild:
                logger.info("删除旧向量数据库...")
                client.delete_collection(name=self.COLLECTION_NAME)
            
            # 创建新集合
            logger.info("创建新向量数据库...")
            collection = client.create_collection(
                name=self.COLLECTION_NAME,
                metadata={
                    "description": "数学教学资源向量数据库",
                    "hnsw:space": "cosine",
                    "hnsw:construction_ef": 200,
                    "hnsw:M": 16
                }
            )
            
            # 解析所有资源汇总表
            logger.info("解析资源汇总表...")
            all_resources = self.parser.parse_all_tables()
            
            # 获取embedding模型
            embedding_model = self.get_embedding_model()
            resource_id = 0
            total_written = 0
            
            # 处理每种类型的资源
            for resource_type, resources in all_resources.items():
                logger.info(f"处理{resource_type}资源，共{len(resources)}条记录...")

                batch_documents = []
                batch_metadatas = []
                batch_ids = []

                for resource in resources:
                    # 格式化资源为搜索文本
                    document = self.parser.format_resource_for_search(resource)
                    
                    # 准备元数据
                    # V62.0改进：使用数据库类型作为resource_type，确保与资源检索器的过滤条件匹配
                    from ..config.resource_type_config import get_db_type
                    db_resource_type = get_db_type(resource_type) or resource_type
                    metadata = {
                        'resource_type': db_resource_type,
                        'source_file': resource.get('source_file', ''),
                        'title': resource.get('title', ''),
                        **{k: v for k, v in resource.items() if k not in ['resource_type', 'source_file', 'title']}
                    }
                    
                    batch_documents.append(document)
                    batch_metadatas.append(metadata)
                    batch_ids.append(f"{resource_type}_{resource_id}")
                    resource_id += 1

                    if len(batch_documents) >= batch_size:
                        logger.info(f"批量生成向量并写库: {resource_type}, 批次大小={len(batch_documents)}")
                        embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
                        collection.add(
                            documents=batch_documents,
                            metadatas=batch_metadatas,
                            ids=batch_ids,
                            embeddings=embeddings
                        )
                        total_written += len(batch_documents)
                        batch_documents = []
                        batch_metadatas = []
                        batch_ids = []

                if batch_documents:
                    logger.info(f"批量生成向量并写库: {resource_type}, 批次大小={len(batch_documents)}")
                    embeddings = embedding_model.encode(batch_documents, normalize_embeddings=True).tolist()
                    collection.add(
                        documents=batch_documents,
                        metadatas=batch_metadatas,
                        ids=batch_ids,
                        embeddings=embeddings
                    )
                    total_written += len(batch_documents)

            if total_written == 0:
                logger.warning("没有找到任何资源文档，向量数据库为空")
                return True
            
            logger.info(f"向量数据库构建完成，共{total_written}条记录")
            logger.info(f"数据库路径: {self.db_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"构建向量数据库失败: {str(e)}")
            return False
    
    def check_database_exists(self) -> bool:
        """
        检查向量数据库是否存在
        
        Returns:
            是否存在
        """
        try:
            client = self.get_chroma_client()
            collections = client.list_collections()
            return any(col.name == self.COLLECTION_NAME for col in collections)
        except Exception as e:
            logger.error(f"检查向量数据库失败: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            client = self.get_chroma_client()
            collection = client.get_collection(name=self.COLLECTION_NAME)
            
            count = collection.count()
            
            # 获取所有资源的类型统计
            results = collection.get(include=['metadatas'])
            type_stats = {}
            
            for metadata in results['metadatas']:
                resource_type = metadata.get('resource_type', 'unknown')
                type_stats[resource_type] = type_stats.get(resource_type, 0) + 1
            
            return {
                'total_count': count,
                'type_stats': type_stats,
                'db_path': str(self.db_path)
            }
            
        except Exception as e:
            logger.error(f"获取向量数据库统计信息失败: {str(e)}")
            return {
                'total_count': 0,
                'type_stats': {},
                'db_path': str(self.db_path),
                'error': str(e)
            }
    
    def reset_database(self) -> bool:
        """
        重置向量数据库
        
        Returns:
            是否重置成功
        """
        try:
            client = self.get_chroma_client()
            
            # 删除集合
            if self.COLLECTION_NAME in [col.name for col in client.list_collections()]:
                client.delete_collection(name=self.COLLECTION_NAME)
                logger.info("向量数据库已删除")
            
            return True
            
        except Exception as e:
            logger.error(f"重置向量数据库失败: {str(e)}")
            return False
