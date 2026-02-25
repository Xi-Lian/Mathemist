"""
模型配置模块

职责：
- 管理所有语言模型的初始化和配置
- 提供统一的模型获取接口
- 实现单例模式管理模型实例

依赖：
- langchain_deepseek
- langchain_openai
- sentence_transformers
- chromadb
- smart_content_processor
"""

import os
# 设置 HuggingFace 镜像源，避免连接超时
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

from pathlib import Path
from typing import Any, Optional

try:
    from langchain_deepseek import ChatDeepSeek
except ImportError:
    ChatDeepSeek = None  # type: ignore[assignment]

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None  # type: ignore[assignment]

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
        
        # LLM提供商配置
        # auto: 优先DeepSeek，若未配置则回退到OpenAI兼容模式
        # deepseek: 强制使用DeepSeek
        # openai_compatible: 强制使用OpenAI兼容模式
        self.LLM_PROVIDER = os.getenv("LLM_PROVIDER", "auto").strip().lower()

        # DeepSeek 配置
        self.DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
        self.DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

        # OpenAI 兼容配置（支持第三方 OpenAI 格式接口）
        self.OPENAI_COMPAT_API_KEY = (
            os.getenv("OPENAI_COMPAT_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or ""
        )
        self.OPENAI_COMPAT_BASE_URL = (
            os.getenv("OPENAI_COMPAT_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or ""
        )
        self.OPENAI_COMPAT_MODEL = (
            os.getenv("OPENAI_COMPAT_MODEL")
            or os.getenv("OPENAI_MODEL")
            or "gpt-4o-mini"
        )
        
        # 模型实例
        self._llm = None
        self._llm_provider_resolved = None
        self._deepseek_llm = None
        self._openai_compat_llm = None
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
        
        # 初始化主LLM
        self._init_llm()
    
    @staticmethod
    def _is_valid_api_key(value: str) -> bool:
        """
        检查 API Key 是否有效（非空且非占位符）
        """
        if not value:
            return False
        if value in {"your-api-key-here", "YOUR_API_KEY"}:
            return False
        return True
    
    def _init_llm(self):
        """
        根据 LLM_PROVIDER 初始化模型
        """
        provider = self.LLM_PROVIDER
        if provider not in {"auto", "deepseek", "openai_compatible"}:
            print(f"⚠️  未知 LLM_PROVIDER={provider}，回退到 auto")
            provider = "auto"
        
        if provider == "deepseek":
            self._init_deepseek_model()
            return
        
        if provider == "openai_compatible":
            self._init_openai_compatible_model()
            return
        
        # auto 模式：优先 DeepSeek，失败后尝试 OpenAI 兼容
        if self._is_valid_api_key(self.DEEPSEEK_API_KEY):
            if self._init_deepseek_model():
                return
            print("⚠️  DeepSeek 初始化失败，尝试 OpenAI 兼容模式")
        
        if self._is_valid_api_key(self.OPENAI_COMPAT_API_KEY):
            self._init_openai_compatible_model()
            return
        
        print("⚠️  未找到可用模型配置，请检查 .env 中的 API Key")
    
    def _init_deepseek_model(self) -> bool:
        """
        初始化 DeepSeek 模型

        Returns:
            是否初始化成功
        """
        if ChatDeepSeek is None:
            print("⚠️  未安装 langchain-deepseek，无法使用 DeepSeek 模型")
            self._deepseek_llm = None
            return False
        
        if not self._is_valid_api_key(self.DEEPSEEK_API_KEY):
            print("⚠️  DeepSeek API Key 未配置")
            self._deepseek_llm = None
            return False
        
        try:
            self._deepseek_llm = ChatDeepSeek(
                model=self.DEEPSEEK_MODEL,
                api_key=self.DEEPSEEK_API_KEY,
                temperature=0.3,
                max_tokens=2000
            )
            self._llm = self._deepseek_llm
            self._llm_provider_resolved = "deepseek"
            print(f"✅ DeepSeek模型初始化成功: {self.DEEPSEEK_MODEL}")
            return True
        except Exception as e:
            print(f"⚠️  DeepSeek模型初始化失败: {e}")
            self._deepseek_llm = None
            return False
    
    def _init_openai_compatible_model(self) -> bool:
        """
        初始化 OpenAI 兼容模型

        Returns:
            是否初始化成功
        """
        if ChatOpenAI is None:
            print("⚠️  未安装 langchain-openai，无法使用 OpenAI 兼容模式")
            self._openai_compat_llm = None
            return False
        
        if not self._is_valid_api_key(self.OPENAI_COMPAT_API_KEY):
            print("⚠️  OpenAI 兼容 API Key 未配置")
            self._openai_compat_llm = None
            return False
        
        try:
            kwargs = {
                "model": self.OPENAI_COMPAT_MODEL,
                "api_key": self.OPENAI_COMPAT_API_KEY,
                "temperature": 0.3,
                "max_tokens": 2000,
            }
            if self.OPENAI_COMPAT_BASE_URL:
                kwargs["base_url"] = self.OPENAI_COMPAT_BASE_URL
            
            self._openai_compat_llm = ChatOpenAI(**kwargs)
            self._llm = self._openai_compat_llm
            self._llm_provider_resolved = "openai_compatible"
            print(f"✅ OpenAI兼容模型初始化成功: {self.OPENAI_COMPAT_MODEL}")
            return True
        except Exception as e:
            print(f"⚠️  OpenAI兼容模型初始化失败: {e}")
            self._openai_compat_llm = None
            return False
    
    def get_deepseek_model(self) -> Any:
        """
        获取 DeepSeek 语言模型
        
        Returns:
            DeepSeek 模型实例
        """
        if self._deepseek_llm is None:
            raise ValueError("DeepSeek模型未初始化，请检查API密钥配置")
        return self._deepseek_llm
    
    def get_openai_compatible_model(self) -> Any:
        """
        获取 OpenAI 兼容模型
        
        Returns:
            OpenAI 兼容模型实例
        """
        if self._openai_compat_llm is None:
            raise ValueError("OpenAI兼容模型未初始化，请检查API密钥配置")
        return self._openai_compat_llm
    
    def get_llm_provider(self) -> str:
        """
        获取当前实际生效的模型提供商
        """
        return self._llm_provider_resolved or "unavailable"
    
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
    
    def get_model(self, task_type: str = "default") -> Any:
        """
        根据任务类型获取合适的模型
        
        Args:
            task_type: 任务类型（当前统一使用同一模型）
        
        Returns:
            模型实例
        """
        if self._llm is None:
            raise ValueError(
                "模型未初始化，请检查 .env："
                "DEEPSEEK_API_KEY（DeepSeek）或 OPENAI_COMPAT_API_KEY（OpenAI兼容）"
            )
        return self._llm


# 全局配置实例
model_config = ModelConfig()


# 向后兼容的函数接口
def get_model(task_type: str = "default") -> Any:
    """
    获取语言模型（向后兼容接口）
    
    Args:
        task_type: 任务类型
    
    Returns:
        模型实例
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
