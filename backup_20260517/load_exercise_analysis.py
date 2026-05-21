#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

class ExerciseAnalysisLoader:
    """
    加载已保存的习题分析结果
    """
    
    def __init__(self, analysis_dir=None):
        if analysis_dir is None:
            self.analysis_dir = os.path.join(
                os.path.dirname(__file__), 
                'learning_resource', 
                'exercise_analysis'
            )
        else:
            self.analysis_dir = analysis_dir
        
        # 缓存已加载的分析结果
        self.analysis_cache = {}
        self._load_all_analysis()
    
    def _load_all_analysis(self):
        """加载所有已保存的分析结果"""
        if not os.path.exists(self.analysis_dir):
            return
        
        for filename in os.listdir(self.analysis_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.analysis_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        exercise_id = data.get('exercise_id')
                        if exercise_id:
                            self.analysis_cache[exercise_id] = data
                except Exception as e:
                    print(f"Failed to load {filename}: {e}")
        
        print("Loaded", len(self.analysis_cache), "analysis results")
    
    def get_analysis(self, resource):
        """
        根据资源获取分析结果
        
        Args:
            resource: 资源字典
        
        Returns:
            分析结果（如果找到），否则返回None
        """
        resource_type = resource.get('resource_type', '')
        source_file = resource.get('source_file', '')
        title = resource.get('title', '')
        
        # 生成ID（与分析时一致）
        exercise_id = f"{resource_type}_{hash(source_file + title) % 100000}"
        
        # 尝试多种ID格式
        possible_ids = [
            exercise_id,
            f"{resource_type.lower()}_{hash(source_file + title) % 100000}",
            f"exercise_{hash(source_file + title) % 100000}",
        ]
        
        for eid in possible_ids:
            if eid in self.analysis_cache:
                return self.analysis_cache[eid].get('analysis')
        
        return None
    
    def get_all_analysis(self):
        """获取所有分析结果"""
        return list(self.analysis_cache.values())
    
    def get_analysis_count(self):
        """获取分析结果数量"""
        return len(self.analysis_cache)

# 测试
if __name__ == "__main__":
    loader = ExerciseAnalysisLoader()
    print("Total analysis results:", loader.get_analysis_count())