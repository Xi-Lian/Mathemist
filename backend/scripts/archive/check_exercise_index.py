#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查习题资源索引情况
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_exercise_index():
    """检查习题资源索引情况"""
    print("=" * 60)
    print("检查习题资源索引情况")
    print("=" * 60)
    
    db_path = r"D:\Git_Repository\Mathemist\backend\chroma_db"
    print("数据库路径:", db_path)
    
    # 1. 检查数据库中的习题资源
    print("\n1. 检查数据库中的习题资源")
    print("-" * 40)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = [
            ('math_resources_function', '函数'),
            ('math_resources_geometry', '几何'),
            ('math_resources_probability', '概率统计'),
            ('math_resources_algebra', '代数'),
            ('math_resources_general', '通用')
        ]
        
        total_exercises = 0
        for col_name, board_name in collections:
            try:
                col = client.get_collection(col_name)
                results = col.get(where={'resource_type': 'exercise'})
                count = len(results['ids'])
                total_exercises += count
                print("板块 %s (%s): %d 条习题" % (board_name, col_name, count))
                
                if count > 0 and results.get('metadatas'):
                    for i, meta in enumerate(results['metadatas'][:2]):
                        title = meta.get('title', '未知')[:40]
                        print("  - %s..." % title)
            except Exception as e:
                print("板块 %s (%s): 错误 - %s" % (board_name, col_name, str(e)[:100]))
        
        print("总计习题资源: %d 条" % total_exercises)
        
    except Exception as e:
        print("连接数据库失败:", str(e)[:200])
        return
    
    # 2. 检查资源表解析器
    print("\n2. 检查资源表解析器")
    print("-" * 40)
    
    try:
        from app.core.resource_table_parser import ResourceTableParser
        
        parser = ResourceTableParser(r"D:\Git_Repository\Mathemist\learning_resource")
        all_resources = parser.parse_all_tables()
        
        print("解析到的资源类型:")
        for resource_type, resources in all_resources.items():
            count = len(resources)
            print("  %s: %d 条" % (resource_type, count))
            
            if resource_type == 'exercise' and count > 0:
                print("    前2个习题:")
                for i, res in enumerate(resources[:2]):
                    title = res.get('title', '未知')[:40]
                    print("      %d. %s..." % (i+1, title))
        
        if 'exercise' not in all_resources or len(all_resources.get('exercise', [])) == 0:
            print("警告: 资源表解析器没有解析到习题资源")
            
    except Exception as e:
        print("资源表解析失败:", str(e)[:200])
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)

if __name__ == "__main__":
    check_exercise_index()