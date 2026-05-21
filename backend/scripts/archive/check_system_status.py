#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
系统状态检查脚本
检查检索配置、知识图谱状态和当前检索效果
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_retrieval_config():
    """检查检索配置"""
    print("=" * 60)
    print("1. 检查检索配置")
    print("=" * 60)
    
    try:
        from app.core.config_manager import config_manager
        
        config = config_manager.get_config()
        
        # 检索相关配置
        retrieval = config.get('retrieval', {})
        print("检索配置:")
        print(f"  相似度阈值: {retrieval.get('similarity_threshold', '未设置')}")
        print(f"  返回结果数: {retrieval.get('n_results', '未设置')}")
        print(f"  语义匹配权重: {retrieval.get('semantic_weight', '未设置')}")
        print(f"  关键词权重: {retrieval.get('keyword_weight', '未设置')}")
        
        # 向量数据库配置
        vector_db = config.get('vector_database', {})
        print("\n向量数据库配置:")
        print(f"  数据库路径: {vector_db.get('path', '未设置')}")
        print(f"  嵌入模型: {vector_db.get('embedding_model', '未设置')}")
        
    except Exception as e:
        print(f"配置读取失败: {e}")

def check_knowledge_graph():
    """检查知识图谱状态"""
    print("\n" + "=" * 60)
    print("2. 检查知识图谱状态")
    print("=" * 60)
    
    try:
        from app.core.knowledge_graph import KnowledgeGraph
        
        kg = KnowledgeGraph()
        
        node_count = kg.get_node_count()
        edge_count = kg.get_edge_count()
        
        print(f"知识图谱状态: ✅ 可用")
        print(f"节点数: {node_count}")
        print(f"边数: {edge_count}")
        
        # 测试查询
        related = kg.get_related_nodes('三角恒等变换')
        print(f"\n与'三角恒等变换'相关的概念:")
        for i, node in enumerate(related[:5]):
            print(f"  {i+1}. {node}")
            
    except ImportError:
        print("❌ 知识图谱模块未找到")
    except AttributeError as e:
        print(f"❌ 知识图谱方法缺失: {e}")
    except Exception as e:
        print(f"❌ 知识图谱加载失败: {e}")

def check_vector_database():
    """检查向量数据库状态"""
    print("\n" + "=" * 60)
    print("3. 检查向量数据库状态")
    print("=" * 60)
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        client = chromadb.PersistentClient(
            path=r'D:\Git_Repository\Mathemist\backend\chroma_db',
            settings=Settings(anonymized_telemetry=False)
        )
        
        collections = client.list_collections()
        print(f"数据库状态: ✅ 可用")
        print(f"集合数: {len(collections)}")
        
        for col in collections:
            # 统计不同资源类型的数量
            try:
                exercise_count = len(col.get(where={'resource_type': 'exercise'})['ids'])
                lesson_plan_count = len(col.get(where={'resource_type': 'lesson_plan'})['ids'])
                courseware_count = len(col.get(where={'resource_type': 'courseware'})['ids'])
                
                print(f"\n集合: {col.name}")
                print(f"  总记录数: {col.count()}")
                print(f"  习题: {exercise_count}")
                print(f"  教案: {lesson_plan_count}")
                print(f"  课件: {courseware_count}")
            except Exception as e:
                print(f"  统计失败: {e}")
                
    except Exception as e:
        print(f"❌ 向量数据库检查失败: {e}")

def test_retrieval():
    """测试当前检索效果"""
    print("\n" + "=" * 60)
    print("4. 测试检索效果")
    print("=" * 60)
    
    try:
        from app.core.retrieval.resource_retriever import ResourceRetriever
        
        retriever = ResourceRetriever()
        results = retriever.retrieve(
            '三角函数恒等变换',
            resource_types=['exercise'],
            n_results=5
        )
        
        docs = results.get('documents', [])
        metadatas = results.get('metadatas', [])
        
        print(f"检索结果数: {len(docs)}")
        
        if docs:
            print("\n前5条结果:")
            for i, doc in enumerate(docs[:5]):
                meta = metadatas[i] if metadatas else {}
                title = meta.get('title', '未知')
                knowledge = meta.get('知识点', '未知')
                
                print(f"\n{i+1}. 标题: {title}")
                print(f"   知识点: {knowledge}")
                print(f"   内容预览: {doc[:100]}...")
                
    except Exception as e:
        print(f"❌ 检索测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_retrieval_config()
    check_knowledge_graph()
    check_vector_database()
    test_retrieval()
    
    print("\n" + "=" * 60)
    print("检查完成")
    print("=" * 60)