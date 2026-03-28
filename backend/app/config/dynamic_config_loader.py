#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
动态配置加载器
用于加载知识点配置和意图模式配置，实现动态、通用的配置管理
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional


class DynamicConfigLoader:
    """
    动态配置加载器
    
    负责加载和管理知识点配置、意图模式配置等
    支持热更新和动态扩展
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if DynamicConfigLoader._initialized:
            return
        
        self.config_dir = Path(__file__).parent
        
        self.knowledge_config: Dict[str, Any] = {}
        self.intent_patterns_config: Dict[str, Any] = {}
        
        self._load_configs()
        
        DynamicConfigLoader._initialized = True
    
    def _load_configs(self):
        """加载所有配置文件"""
        self._load_knowledge_config()
        self._load_intent_patterns_config()
    
    def _load_knowledge_config(self):
        """加载知识点配置"""
        config_path = self.config_dir / "knowledge_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.knowledge_config = json.load(f)
        else:
            self.knowledge_config = {
                "knowledge_hierarchy": {},
                "parent_topics": {},
                "grade_mapping": {}
            }
    
    def _load_intent_patterns_config(self):
        """加载意图模式配置"""
        config_path = self.config_dir / "intent_patterns_config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.intent_patterns_config = json.load(f)
        else:
            self.intent_patterns_config = {
                "intent_patterns": {},
                "priority_levels": {}
            }
    
    def reload_configs(self):
        """重新加载所有配置文件"""
        self._load_configs()
        print("✅ 配置文件已重新加载")
    
    def get_knowledge_hierarchy(self) -> Dict[str, Any]:
        """获取知识点层级结构"""
        return self.knowledge_config.get("knowledge_hierarchy", {})
    
    def get_parent_topics(self) -> Dict[str, Any]:
        """获取父级主题"""
        return self.knowledge_config.get("parent_topics", {})
    
    def get_grade_mapping(self) -> Dict[str, List[str]]:
        """获取年级映射"""
        return self.knowledge_config.get("grade_mapping", {})
    
    def get_intent_patterns(self) -> Dict[str, Any]:
        """获取意图模式"""
        return self.intent_patterns_config.get("intent_patterns", {})
    
    def get_priority_levels(self) -> Dict[str, int]:
        """获取优先级级别"""
        return self.intent_patterns_config.get("priority_levels", {})
    
    def get_all_themes(self) -> List[str]:
        """获取所有主题名称"""
        return list(self.knowledge_config.get("knowledge_hierarchy", {}).keys())
    
    def get_theme_keywords(self, theme: str) -> List[str]:
        """获取指定主题的关键词"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("keywords", [])
        return []
    
    def get_theme_chapters(self, theme: str) -> List[str]:
        """获取指定主题的章节"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("chapters", [])
        return []
    
    def get_theme_parent_topic(self, theme: str) -> Optional[str]:
        """获取指定主题的父级主题"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("parent_topic")
        return None
    
    def get_theme_grade_level(self, theme: str) -> List[str]:
        """获取指定主题的适用年级"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("grade_level", [])
        return []
    
    def get_all_keywords(self) -> List[str]:
        """获取所有主题的所有关键词"""
        all_keywords = []
        hierarchy = self.get_knowledge_hierarchy()
        for theme_info in hierarchy.values():
            all_keywords.extend(theme_info.get("keywords", []))
        return list(set(all_keywords))
    
    def get_themes_by_parent_topic(self, parent_topic: str) -> List[str]:
        """根据父级主题获取子主题列表"""
        themes = []
        hierarchy = self.get_knowledge_hierarchy()
        for theme, info in hierarchy.items():
            if info.get("parent_topic") == parent_topic:
                themes.append(theme)
        return themes
    
    def get_themes_by_grade(self, grade: str) -> List[str]:
        """根据年级获取适用的主题列表"""
        themes = []
        hierarchy = self.get_knowledge_hierarchy()
        for theme, info in hierarchy.items():
            if grade in info.get("grade_level", []):
                themes.append(theme)
        return themes
    
    def get_function_related_themes(self) -> List[str]:
        """获取函数相关的主题列表"""
        return self.get_themes_by_parent_topic("函数")
    
    def is_function_related_theme(self, theme: str) -> bool:
        """判断主题是否为函数相关"""
        parent_topic = self.get_theme_parent_topic(theme)
        return parent_topic == "函数"
    
    def search_themes_by_keyword(self, keyword: str) -> List[str]:
        """根据关键词搜索主题"""
        matched_themes = []
        hierarchy = self.get_knowledge_hierarchy()
        for theme, info in hierarchy.items():
            if keyword in info.get("keywords", []):
                matched_themes.append(theme)
        return matched_themes
    
    def get_intent_priority(self, intent_name: str) -> int:
        """获取意图的优先级"""
        patterns = self.get_intent_patterns()
        if intent_name in patterns:
            return patterns[intent_name].get("priority", 5)
        return 5
    
    def get_intent_patterns_by_name(self, intent_name: str) -> Dict[str, Any]:
        """根据意图名称获取意图模式"""
        patterns = self.get_intent_patterns()
        return patterns.get(intent_name, {})
    
    def get_all_function_types(self) -> List[str]:
        """
        V61.0改进：动态获取所有函数类型主题
        用于替换硬编码的函数类型列表
        """
        return self.get_themes_by_parent_topic("函数")
    
    def get_theme_keywords(self, theme: str) -> List[str]:
        """获取指定主题的关键词列表"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("keywords", [])
        return []
    
    def get_theme_chapters(self, theme: str) -> List[str]:
        """获取指定主题的章节列表"""
        hierarchy = self.get_knowledge_hierarchy()
        if theme in hierarchy:
            return hierarchy[theme].get("chapters", [])
        return []
    
    def get_all_theme_keywords_flat(self) -> List[str]:
        """
        获取所有主题的关键词（扁平化列表）
        用于关键词匹配
        """
        all_keywords = []
        hierarchy = self.get_knowledge_hierarchy()
        for theme, info in hierarchy.items():
            all_keywords.extend(info.get("keywords", []))
        return list(set(all_keywords))
    
    def get_unrelated_themes_for_filter(self, query_themes: List[str]) -> List[str]:
        """
        V61.0改进：动态获取需要过滤的非查询主题
        用于替换硬编码的 unrelated_themes_check 列表
        
        Args:
            query_themes: 查询中包含的主题列表
        
        Returns:
            需要过滤的主题列表
        """
        all_function_types = self.get_all_function_types()
        return [t for t in all_function_types if t not in query_themes]


_config_loader = None


def get_config_loader() -> DynamicConfigLoader:
    """获取配置加载器单例"""
    global _config_loader
    if _config_loader is None:
        _config_loader = DynamicConfigLoader()
    return _config_loader
