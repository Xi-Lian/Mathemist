#!/usr/bin/env python
import logging
from typing import Dict, Any, Optional, List
from ..cache_manager import CacheManager
from .methods.retrieve import _RetrieveMixin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class OptimizedResourceRetriever(_RetrieveMixin):
    _instance = None
    _lock = __import__('threading').Lock()
    
    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        super().__init__()
        self.cache_manager = CacheManager()
        self._initialized = True
        logger.info("✅ OptimizedResourceRetriever 初始化完成（单例模式）")
    
    def retrieve_with_cache(
        self,
        query: str,
        intent: str = "search",
        n_results: int = None,
        resource_types: List[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        cache_result = self.cache_manager.get_query_result(query)
        if cache_result:
            logger.info(f"📦 命中查询缓存: {query[:30]}...")
            return cache_result
        
        result = self.retrieve(
            query=query,
            intent=intent,
            n_results=n_results,
            resource_types=resource_types,
            **kwargs
        )
        
        self.cache_manager.set_query_result(query, result)
        return result
    
    def get_llm_result_with_cache(self, prompt: str) -> Optional[str]:
        cached = self.cache_manager.get_llm_result(prompt)
        if cached:
            logger.info(f"📦 命中LLM缓存: {prompt[:30]}...")
            return cached
        return None
    
    def set_llm_result_cache(self, prompt: str, result: str):
        self.cache_manager.set_llm_result(prompt, result)
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            **self.cache_manager.get_stats(),
            'is_singleton': True
        }
