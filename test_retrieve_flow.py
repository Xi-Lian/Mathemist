#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, 'backend')

from app.core.retrieval.methods.retrieve import _RetrieveMixin

print("=" * 60)
print("测试完整检索流程")
print("=" * 60)

query = "线面角"
core_theme = "线面角"

print(f"\n搜索查询: '{query}'")
print(f"核心主题: '{core_theme}'")

retriever = _RetrieveMixin()

# 执行检索
results = retriever.retrieve(
    query=query,
    intent="search",
    n_results=10,
    resource_types=["exercise"],
    quantity_limit=None,
    grade_info=None,
    clarified_topic=None,
    difficulty_info=None
)

# 提取习题结果
exercise_results = results.get('exercise_resources', [])
print(f"\n检索返回的习题数量: {len(exercise_results)}")

if exercise_results:
    for i, result in enumerate(exercise_results[:5]):
        title = result.get('title', '')
        score = result.get('score', 0)
        final_score = result.get('final_score', 0)
        resource_type = result.get('resource_type', '')
        
        print(f"\n{i+1}. {title}")
        print(f"   类型: {resource_type}")
        print(f"   分数: {score:.4f}")
        print(f"   最终分数: {final_score:.4f}")
        
        # 检查知识点
        metadata = result.get('metadata', {})
        analysis_json = metadata.get('analysis_json', '')
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
