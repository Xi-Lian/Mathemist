"""
模型配置模块

职责：
- 管理所有语言模型的初始化和配置
- 提供统一的模型获取接口
- 实现单例模式管理模型实例

依赖：
- langchain_deepseek
- sentence_transformers
- chromadb
- smart_content_processor
"""

import os
# 设置 HuggingFace 镜像源，避免连接超时
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from pathlib import Path
from typing import Optional
from langchain_deepseek import ChatDeepSeek
from sentence_transformers import SentenceTransformer
import chromadb
from ..smart_content_processor import SmartContentProcessor


class ModelConfig:
    """模型配置管理类（单例模式）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # DeepSeek配置
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
        self.DEEPSEEK_MODEL = "deepseek-chat"
        
        # 模型实例
        self._deepseek_llm = None
        self._embedding_model = None
        self._chroma_client = None
        self._content_processor = None
        
        # 路径配置
        self.SCRIPT_DIR = Path(__file__).parent.parent.parent.parent
        self.CHROMA_DB_DIR = self.SCRIPT_DIR / "backend" / "chroma_db"
        self.EMBEDDING_MODEL_PATH = os.getenv(
            "EMBEDDING_MODEL_PATH", 
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
        
        # 初始化DeepSeek模型
        self._init_deepseek_model()
    
    def _init_deepseek_model(self):
        """初始化DeepSeek模型"""
        try:
            self._deepseek_llm = ChatDeepSeek(
                model=self.DEEPSEEK_MODEL,
                api_key=self.DEEPSEEK_API_KEY,
                temperature=0.3,
                max_tokens=2000
            )
            print("✅ DeepSeek模型初始化成功")
        except Exception as e:
            print(f"⚠️  DeepSeek模型初始化失败: {e}")
            self._deepseek_llm = None
    
    def get_deepseek_model(self) -> Optional[ChatDeepSeek]:
        """
        获取DeepSeek语言模型
        
        Returns:
            ChatDeepSeek实例，如果初始化失败则返回None
        """
        if self._deepseek_llm is None:
            raise ValueError("DeepSeek模型未初始化，请检查API密钥配置")
        return self._deepseek_llm
    
    def get_embedding_model(self) -> SentenceTransformer:
        """
        获取Embedding模型（单例模式）
        
        Returns:
            SentenceTransformer实例
        """
        if self._embedding_model is None:
            try:
                self._embedding_model = SentenceTransformer(self.EMBEDDING_MODEL_PATH)
                print("✅ Embedding模型初始化成功")
            except Exception as e:
                print(f"⚠️  Embedding模型初始化失败: {e}")
                raise ValueError(f"Embedding模型初始化失败: {e}")
        return self._embedding_model
    
    def get_chroma_client(self) -> chromadb.PersistentClient:
        """
        获取ChromaDB客户端（单例模式）
        
        Returns:
            ChromaDB客户端实例
        """
        if self._chroma_client is None:
            self._chroma_client = chromadb.PersistentClient(path=str(self.CHROMA_DB_DIR))
            print(f"✅ ChromaDB客户端初始化成功: {self.CHROMA_DB_DIR}")
        return self._chroma_client
    
    def get_content_processor(self) -> SmartContentProcessor:
        """
        获取智能内容处理器（单例模式）
        
        Returns:
            SmartContentProcessor实例
        """
        if self._content_processor is None:
            self._content_processor = SmartContentProcessor()
            print("✅ 智能内容处理器初始化成功")
        return self._content_processor
    
    def get_model(self, task_type: str = "default") -> ChatDeepSeek:
        """
        根据任务类型获取合适的模型
        
        Args:
            task_type: 任务类型（当前统一使用DeepSeek）
        
        Returns:
            ChatDeepSeek实例
        """
        return self.get_deepseek_model()


# 全局配置实例
model_config = ModelConfig()


# 向后兼容的函数接口
def get_model(task_type: str = "default") -> ChatDeepSeek:
    """
    获取语言模型（向后兼容接口）
    
    Args:
        task_type: 任务类型
    
    Returns:
        ChatDeepSeek实例
    """
    return model_config.get_model(task_type)


def get_embedding_model() -> SentenceTransformer:
    """
    获取Embedding模型（向后兼容接口）
    
    Returns:
        SentenceTransformer实例
    """
    return model_config.get_embedding_model()


def get_chroma_client() -> chromadb.PersistentClient:
    """
    获取ChromaDB客户端（向后兼容接口）
    
    Returns:
        ChromaDB客户端实例
    """
    return model_config.get_chroma_client()


def get_content_processor() -> SmartContentProcessor:
    """
    获取智能内容处理器（向后兼容接口）
    
    Returns:
        SmartContentProcessor实例
    """
    return model_config.get_content_processor()
