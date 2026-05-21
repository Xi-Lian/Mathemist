#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.simple_exercise_retrieval import simple_exercise_retrieval
from app.core.vector_database_builder import VectorDatabaseBuilder

print("=" * 60)
print("测试简单习题检索")
print("=" * 60)

builder = VectorDatabaseBuilder('learning_resource')
vector_db = builder.get_chroma_client()

query = "线面角"
core_theme = "线面角"

print(f"\n搜索查询: '{query}'")
print(f"核心主题: '{core_theme}'")

results = simple_exercise_retrieval(
    query=query,
    core_theme=core_theme,
    vector_db=vector_db,
    n_results=10,
    resource_types=["exercise"]
)

print(f"\n检索返回的习题数量: {len(results)}")

if results:
    for i, result in enumerate(results[:5]):
        meta = result.get('metadata', {})
        title = meta.get('title', '')
        score = result.get('score', 0)
        
        print(f"\n{i+1}. {title}")
        print(f"   分数: {score:.4f}")
        
        # 检查知识点
        analysis_json = meta.get('analysis_json', '')
        if analysis_json:
            try:
                import json
                analysis = json.loads(analysis_json)
                if isinstance(analysis, dict):
                    kp_list = analysis.get('知识点', [])
                    print(f"   知识点: {kp_list}")
                    has_line_angle = any('线面角' in kp for kp in kp_list)
                    print(f"   包含线面角知识点: {'是' if has_line_angle else '否'}")
            except Exception as e:
                print(f"   解析知识点失败: {e}")

else:
    print("\n未找到匹配的资源")
    
    # 检查数据库中是否存在相关内容
    print("\n" + "=" * 60)
    print("检查数据库内容...")
    
    import chromadb
    from chromadb.config import Settings
    
    client = chromadb.PersistentClient(
        path='backend/chroma_db',
        settings=Settings(anonymized_telemetry=False)
    )
    
    collection = client.get_collection('math_resources_geometry')
    count = collection.count()
    print(f"几何集合文档数: {count}")
    
    # 搜索包含线面角的文档
    results = collection.query(
        query_texts=["线面角"],
        n_results=10,
        include=["metadatas", "documents"]
    )
    
    print(f"\n向量搜索返回: {len(results['metadatas'][0])} 条")
    
    if results['metadatas'][0]:
        for meta in results['metadatas'][0][:3]:
            print(f"\n标题: {meta.get('title', '')}")
            analysis_json = meta.get('analysis_json', '')
            if analysis_json:
                try:
                    import json
                    analysis = json.loads(analysis_json)
                    if isinstance(analysis, dict):
                        print(f"知识点: {analysis.get('知识点', [])}")
                except:
                    pass

print("\n" + "=" * 60)
print("测试完成")
