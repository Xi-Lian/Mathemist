#!/usr/bin/env python
import jieba
import hashlib
from typing import Optional, Dict, Any
import time

class CacheManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        self.llm_cache = {}
        self.query_cache = {}
        self.jieba_loaded = False
        self._load_jieba()
    
    def _load_jieba(self):
        if not self.jieba_loaded:
            jieba.initialize()
            self.jieba_loaded = True
    
    def get_cache_key(self, text: str) -> str:
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def get_llm_result(self, prompt: str) -> Optional[str]:
        key = self.get_cache_key(prompt)
        item = self.llm_cache.get(key)
        if item:
            if time.time() < item['expire']:
                return item['value']
            else:
                del self.llm_cache[key]
        return None
    
    def set_llm_result(self, prompt: str, result: str, ttl: int = 300):
        key = self.get_cache_key(prompt)
        self.llm_cache[key] = {
            'value': result,
            'expire': time.time() + ttl
        }
    
    def get_query_result(self, query: str) -> Optional[Dict]:
        key = self.get_cache_key(query)
        item = self.query_cache.get(key)
        if item:
            if time.time() < item['expire']:
                return item['value']
            else:
                del self.query_cache[key]
        return None
    
    def set_query_result(self, query: str, result: Dict, ttl: int = 600):
        key = self.get_cache_key(query)
        self.query_cache[key] = {
            'value': result,
            'expire': time.time() + ttl
        }
    
    def clear_all(self):
        self.llm_cache.clear()
        self.query_cache.clear()
    
    def get_stats(self) -> Dict[str, int]:
        return {
            'llm_cache_size': len(self.llm_cache),
            'query_cache_size': len(self.query_cache),
            'jieba_loaded': self.jieba_loaded
        }
