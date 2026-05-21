#!/usr/bin/env python
import threading
from typing import Optional

class SingletonMeta(type):
    _instances = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]

class CachedRetriever(metaclass=SingletonMeta):
    def __init__(self):
        self.retrievers = {}
        self.llm_cache = {}
        self.query_cache = {}
        
    def get_retriever(self, collection_name: str):
        if collection_name not in self.retrievers:
            from .methods.retrieve import ResourceRetriever
            self.retrievers[collection_name] = ResourceRetriever(collection_name)
        return self.retrievers[collection_name]
    
    def get_llm_cache(self, key: str) -> Optional[str]:
        return self.llm_cache.get(key)
    
    def set_llm_cache(self, key: str, value: str, ttl: int = 300):
        self.llm_cache[key] = value
        
    def get_query_cache(self, query: str) -> Optional[dict]:
        return self.query_cache.get(query)
    
    def set_query_cache(self, query: str, result: dict, ttl: int = 600):
        self.query_cache[query] = result
        
    def clear_cache(self):
        self.llm_cache.clear()
        self.query_cache.clear()
