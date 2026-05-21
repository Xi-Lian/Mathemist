#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查真正的习题资源数据结构
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_exercise_details():
    """检查习题资源的详细数据结构"""
    print("=" * 60)
    print("检查真正的习题资源数据结构")
    print("=" * 60)
    
    try:
        from app.core.model_config import model_config
        
        # 获取向量数据库客户端
        vector_db = model_config.get_chroma_client()
        
        # 获取函数板块集合
        collection = vector_db.get_collection('math_resources_function')
        
        # 查询所有exercise类型的资源
        results = collection.get(
            where={"resource_type": "exercise"},
            include=['documents', 'metadatas']
        )
        
        docs = results['documents']
        metas = results['metadatas']
        
        print("找到 %d 条 exercise 类型资源" % len(docs))
        print("-" * 60)
        
        # 统计分析
        with_stem = 0
        with_image = 0
        stem_only = 0
        image_only = 0
        
        for i, (doc, meta) in enumerate(zip(docs, metas)):
            title = meta.get('title', '空')
            question = meta.get('题干', '').strip()
            filename = meta.get('题目文件名', '').strip()
            resource_type = meta.get('resource_type', '空')
            
            has_stem = len(question) > 0
            has_image = len(filename) > 0 and (filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'))
            
            if has_stem:
                with_stem += 1
            if has_image:
                with_image += 1
            if has_stem and not has_image:
                stem_only += 1
            if has_image and not has_stem:
                image_only += 1
            
            # 只显示前5条详细信息
            if i < 5:
                print("资源 %d:" % (i+1))
                print("  标题: %s" % title)
                print("  资源类型: %s" % resource_type)
                print("  有题干: %s" % ("是" if has_stem else "否"))
                if has_stem:
                    print("  题干长度: %d" % len(question))
                    print("  题干预览: %s..." % question[:100])
                print("  有图片: %s" % ("是" if has_image else "否"))
                if has_image:
                    print("  图片文件名: %s" % filename)
                print()
        
        print("统计结果:")
        print("-" * 60)
        print("总习题数: %d" % len(docs))
        print("有题干: %d" % with_stem)
        print("有图片: %d" % with_image)
        print("只有题干: %d" % stem_only)
        print("只有图片: %d" % image_only)
        print("既有题干又有图片: %d" % (with_stem + with_image - len(docs)))
        
    except Exception as e:
        print("检查失败: %s" % str(e))
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_exercise_details()
    print("=" * 60)
    print("检查完成")
    print("=" * 60)
