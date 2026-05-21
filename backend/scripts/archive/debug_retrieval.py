#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
习题检索排查脚本
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_database_stats():
    """检查数据库统计信息"""
    print("=" * 60)
    print("步骤1: 检查向量数据库状态")
    print("=" * 60)
    
    try:
        from app.core.vector_database_builder import VectorDatabaseBuilder
        learning_resource_path = r"D:\Git_Repository\Mathemist\learning_resource"
        builder = VectorDatabaseBuilder(learning_resource_path)
        stats = builder.get_collection_stats()
        print("总资源数:", stats.get('count', 0))
    except Exception as e:
        print("错误:", str(e)[:200])

def check_exercise_count():
    """检查习题资源数量"""
    print("\n" + "=" * 60)
    print("步骤2: 检查习题资源数量")
    print("=" * 60)
    
    try:
        from chromadb import Client
        client = Client()
        
        try:
            collection = client.get_collection('math_resources')
            results = collection.get(where={'resource_type': 'exercise'})
            print("习题资源数量:", len(results['ids']))
            
            if results['metadatas']:
                print("\n前3个习题:")
                for i, meta in enumerate(results['metadatas'][:3]):
                    title = meta.get('title', '未知')
                    print("  %d. %s" % (i+1, title))
        except Exception as e:
            print("获取习题失败:", str(e)[:200])
            
    except Exception as e:
        print("连接数据库失败:", str(e)[:200])

def check_excel_tables():
    """检查Excel表格"""
    print("\n" + "=" * 60)
    print("步骤3: 检查Excel表格解析")
    print("=" * 60)
    
    try:
        import pandas as pd
        
        excel_files = [
            r'd:\Git_Repository\Mathemist\learning_resource\函数习题_云端资源汇总表.xlsx',
            r'd:\Git_Repository\Mathemist\learning_resource\概率与统计习题_云端资源汇总表.xlsx',
            r'd:\Git_Repository\Mathemist\learning_resource\立体几何习题_云端资源汇总表.xlsx'
        ]
        
        for excel_file in excel_files:
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file)
                print("存在:", os.path.basename(excel_file))
                print("  行数:", len(df), ", 列数:", len(df.columns))
                print("  列名:", list(df.columns)[:5], "...")
            else:
                print("不存在:", os.path.basename(excel_file))
                
    except Exception as e:
        print("错误:", str(e)[:200])

def test_retrieval():
    """测试检索功能"""
    print("\n" + "=" * 60)
    print("步骤4: 测试检索功能")
    print("=" * 60)
    
    try:
        from app.core.retrieval.resource_retriever import ResourceRetriever
        
        retriever = ResourceRetriever()
        results = retriever.retrieve('三角函数恒等变换', resource_types=['exercise'])
        
        docs = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        print("检索结果数:", len(docs))
        
        if docs:
            print("\n检索到的资源:")
            for i, doc in enumerate(docs[:3]):
                meta = metadatas[i] if metadatas else {}
                title = meta.get('title', '未知')
                knowledge = meta.get('知识点', '未知')
                print("\n  %d. 标题: %s" % (i+1, title))
                print("     知识点: %s" % knowledge)
                print("     内容预览: %s..." % doc[:80])
        else:
            print("未检索到任何资源")
            
    except Exception as e:
        print("检索失败:", str(e)[:200])

if __name__ == "__main__":
    check_database_stats()
    check_exercise_count()
    check_excel_tables()
    test_retrieval()
    
    print("\n" + "=" * 60)
    print("排查完成")
    print("=" * 60)