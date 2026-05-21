#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
知识图谱整合脚本
将知识图谱功能整合到检索流程中
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def integrate_kg_to_retrieve():
    """将知识图谱整合到检索流程"""
    print("整合知识图谱到检索流程...")
    
    # 读取 retrieve.py
    retrieve_path = "app/core/retrieval/methods/retrieve.py"
    
    with open(retrieve_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 添加知识图谱导入
    if 'from ..knowledge_graph import KnowledgeGraph' not in content:
        # 在现有导入后添加
        content = content.replace(
            'from ..retrieve_helpers.single_theme import (',
            'from ..knowledge_graph import KnowledgeGraph\nfrom ..retrieve_helpers.single_theme import ('
        )
    
    # 添加知识图谱初始化
    if 'self.kg = KnowledgeGraph()' not in content:
        # 在 _RetrieveMixin 类的开头添加
        content = content.replace(
            'class _RetrieveMixin:',
            'class _RetrieveMixin:\n    def __init__(self):\n        self.kg = KnowledgeGraph()  # 知识图谱实例'
        )
    
    # 添加查询扩展
    if 'expanded_query = self.kg.expand_query(query)' not in content:
        # 在 semantic matching debug 部分添加知识图谱扩展
        content = content.replace(
            'logger.info("=== 语义匹配调试 - retrieve() 方法被调用 ===")',
            '''logger.info("=== 知识图谱增强检索 ===")
            # 使用知识图谱扩展查询
            expanded_query = self.kg.expand_query(query)
            related_concepts = self.kg.get_related_nodes(query)
            logger.info(f"原始查询: {query}")
            logger.info(f"扩展查询: {expanded_query}")
            logger.info(f"相关概念: {related_concepts}")
            # 使用扩展查询进行检索
            self._current_query = expanded_query
            logger.info("=== 语义匹配调试 - retrieve() 方法被调用 ===")'''
        )
    
    # 保存修改
    with open(retrieve_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("知识图谱整合完成！")

def test_integration():
    """测试知识图谱整合效果"""
    print("\n测试知识图谱整合...")
    
    try:
        from app.core.retrieval.methods.retrieve import _RetrieveMixin
        
        # 创建实例，测试知识图谱是否正确初始化
        mixin = _RetrieveMixin()
        print(f"知识图谱节点数: {mixin.kg.get_node_count()}")
        print(f"知识图谱边数: {mixin.kg.get_edge_count()}")
        
        # 测试查询扩展
        query = "三角函数恒等变换"
        expanded = mixin.kg.expand_query(query)
        print(f"\n原始查询: {query}")
        print(f"扩展查询: {expanded}")
        
        print("\n知识图谱整合测试成功！")
        
    except Exception as e:
        print(f"测试失败: {str(e)[:100]}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    integrate_kg_to_retrieve()
    test_integration()