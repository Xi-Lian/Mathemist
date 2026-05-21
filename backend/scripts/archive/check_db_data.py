#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查向量数据库中的习题数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_exercise_data():
    """检查数据库中的习题数据"""
    print("=" * 60)
    print("检查向量数据库中的习题数据")
    print("=" * 60)
    
    try:
        from app.core.model_config import model_config
        
        # 获取向量数据库客户端
        vector_db = model_config.get_chroma_client()
        
        # 获取函数板块集合（三角恒等变换属于函数板块）
        collection = vector_db.get_collection('math_resources_function')
        
        # 查询三角恒等变换相关的资源
        results = collection.query(
            query_texts=['三角恒等变换', '三角函数'],
            n_results=10,
            include=['documents', 'metadatas']
        )
        
        docs = results['documents'][0]
        metas = results['metadatas'][0]
        
        print("检索到 %d 条资源" % len(docs))
        print("-" * 60)
        
        empty_title_count = 0
        empty_question_count = 0
        empty_knowledge_count = 0
        
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            title = meta.get('title', '空')
            question = meta.get('题干', '')
            question_type = meta.get('题目类型', '空')
            knowledge = meta.get('知识点', '空')
            resource_type = meta.get('resource_type', '空')
            
            print("资源 %d:" % (i+1))
            print("  标题: %s" % title)
            print("  资源类型: %s" % resource_type)
            print("  题目类型: %s" % question_type)
            print("  知识点: %s" % knowledge)
            print("  题干长度: %d 字符" % len(question))
            if question:
                print("  题干预览: %s..." % question[:100])
            else:
                print("  题干: 空")
                empty_question_count += 1
            print()
            
            # 检查是否有内容缺失
            if not title or title == '习题: ':
                empty_title_count += 1
                print("  警告: 标题为空或格式异常")
            if not knowledge:
                empty_knowledge_count += 1
                print("  警告: 知识点为空")
            print()
        
        print("统计结果:")
        print("-" * 60)
        print("总资源数: %d" % len(docs))
        print("标题异常: %d" % empty_title_count)
        print("题干为空: %d" % empty_question_count)
        print("知识点为空: %d" % empty_knowledge_count)
        
    except Exception as e:
        print("检查失败: %s" % str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_exercise_data()
    print("=" * 60)
    print("检查完成")
    print("=" * 60)
