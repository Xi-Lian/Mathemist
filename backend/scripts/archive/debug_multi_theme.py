#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细调试多主题检索流程
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.app.core.retrieval.service import ResourceRetriever
from backend.app.core.retrieval.retrieve_helpers.multi_theme import execute_multi_theme_retrieval
from backend.app.core.vector_database_builder import VectorDatabaseBuilder


def debug_multi_theme_retrieval():
    """详细调试多主题检索"""
    print("\n=== 详细调试多主题检索 ===")
    
    # 测试查询
    test_query = "分别找一下三角函数、分层抽样和离散型随机变量的教案"
    print(f"测试查询: {test_query}")
    
    # 初始化检索器
    retriever = ResourceRetriever()
    
    # 提取核心主题
    core_theme = retriever._extract_core_theme(test_query)
    print(f"提取的核心主题: {core_theme}")
    
    # 处理核心主题
    core_themes = []
    if isinstance(core_theme, tuple) and len(core_theme) == 2:
        theme_str, board_from_tuple = core_theme
        print(f"检测到 core_theme 是元组，theme_str: {theme_str}, board_from_tuple: {board_from_tuple}")
        # 将逗号分隔的主题字符串拆分为列表
        if isinstance(theme_str, str) and "," in theme_str:
            core_themes = [t.strip() for t in theme_str.split(",") if t.strip()]
            print(f"拆分后的 core_themes: {core_themes}")
        elif isinstance(theme_str, str):
            core_themes = [theme_str]
            print(f"单个主题的 core_themes: {core_themes}")
    
    # 提取资源类型
    resource_types = retriever._extract_resource_types_from_query(test_query)
    print(f"提取的资源类型: {resource_types}")
    
    # 提取问题类型
    question_type = retriever._extract_question_type(test_query)
    print(f"提取的问题类型: {question_type}")
    
    # 确保集合就绪
    # 对于多主题检索，我们使用默认集合，因为每个主题会有自己的集合
    from backend.app.core.vector_database_builder import VectorDatabaseBuilder
    builder = VectorDatabaseBuilder("../learning_resource")
    client = builder.get_chroma_client()
    collection = client.get_collection(name="math_resources")
    
    # 执行多主题检索
    print("\n执行多主题检索...")
    results = execute_multi_theme_retrieval(
        retriever,
        collection,
        test_query,
        (core_themes, "函数"),  # 传递正确的元组格式 (主题列表, 板块名称)
        None,
        resource_types,
        question_type,
    )
    
    print(f"\n多主题检索结果:")
    print(f"总结果数: {len(results.get('documents', [[]])[0])}")
    
    if results.get('metadatas') and results['metadatas'][0]:
        print("\n前5个结果:")
        for i, meta in enumerate(results['metadatas'][0][:5]):
            title = meta.get('title', '未知标题')
            source_file = meta.get('source_file', '未知来源')
            resource_type = meta.get('resource_type', '未知类型')
            print(f"[{i+1}] {title} (类型: {resource_type}, 来源: {source_file})")


def test_single_theme_retrieval():
    """测试单主题检索"""
    print("\n=== 测试单主题检索 ===")
    
    test_themes = ["三角函数", "分层抽样", "离散型随机变量"]
    
    for theme in test_themes:
        print(f"\n测试主题: {theme}")
        
        # 初始化检索器
        retriever = ResourceRetriever()
        
        # 执行检索
        results = retriever.retrieve(f"{theme} 教案")
        
        print(f"检索结果数量: {len(results.get('lesson_plan_patterns', []))}")
        
        if results.get('lesson_plan_patterns'):
            print("前3个教案资源:")
            for i, resource in enumerate(results['lesson_plan_patterns'][:3]):
                title = resource.get('title', '未知标题')
                source_file = resource.get('source_file', '未知来源')
                print(f"[{i+1}] {title} (来源: {source_file})")


def test_direct_collection_query():
    """直接测试集合查询"""
    print("\n=== 直接测试集合查询 ===")
    
    # 初始化构建器
    builder = VectorDatabaseBuilder("../learning_resource")
    client = builder.get_chroma_client()
    
    # 测试不同集合的查询
    test_cases = [
        ("math_resources_function", "三角函数 教案"),
        ("math_resources_probability", "分层抽样 教案"),
        ("math_resources_general", "离散型随机变量 教案"),
    ]
    
    for collection_name, query_text in test_cases:
        try:
            collection = client.get_collection(name=collection_name)
            print(f"\n集合: {collection_name}, 查询: {query_text}")
            
            # 执行查询
            results = collection.query(
                query_texts=[query_text],
                n_results=10,
                where={"resource_type": "lesson_plan"},
                include=["metadatas"]
            )
            
            if results.get("metadatas") and results["metadatas"][0]:
                print(f"找到 {len(results['metadatas'][0])} 条结果")
                for i, meta in enumerate(results["metadatas"][0][:3]):
                    title = meta.get('title', '未知标题')
                    source_file = meta.get('source_file', '未知来源')
                    print(f"  [{i+1}] {title} (来源: {source_file})")
            else:
                print("未找到结果")
                
        except Exception as e:
            print(f"集合 {collection_name} 查询失败: {str(e)}")


if __name__ == "__main__":
    print("开始详细调试多主题检索...")
    
    # 测试单主题检索
    test_single_theme_retrieval()
    
    # 直接测试集合查询
    test_direct_collection_query()
    
    # 详细调试多主题检索
    debug_multi_theme_retrieval()
    
    print("\n调试完成!")
