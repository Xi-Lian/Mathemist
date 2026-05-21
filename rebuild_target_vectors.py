#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新构建向量数据库中那两条目标习题的向量
"""
import sys
sys.path.insert(0, 'backend')

from app.core.vector_database_builder import VectorDatabaseBuilder
from app.core.model_config import model_config

def rebuild_target_exercises():
    """重建目标习题的向量"""
    
    print("="*80)
    print("重新构建目标习题的向量")
    print("="*80)
    
    # 创建VectorDatabaseBuilder
    builder = VectorDatabaseBuilder('learning_resource')
    
    # 获取ChromaDB客户端和集合
    client = builder.get_chroma_client()
    col = client.get_or_create_collection('math_resources_function')
    
    # 目标习题ID
    target_ids = ['函数_exercise_205', '函数_exercise_210']
    
    print(f"\n目标习题ID: {target_ids}")
    
    # 获取当前习题的metadata
    for target_id in target_ids:
        result = col.get(ids=[target_id], include=['metadatas'])
        if result['metadatas']:
            meta = result['metadatas'][0]
            print(f"\n{target_id}:")
            print(f"  知识点标签: {meta.get('知识点标签', '')}")
            print(f"  Title: {meta.get('title', '')}")
            print(f"  Source: {meta.get('source_file', '')}")
    
    print("\n\n注意：要完全应用V101.0的修改，需要重新构建整个向量数据库")
    print("因为format_resource_for_search是在构建向量时调用的")
    print("\n建议操作：")
    print("1. 停止后端服务")
    print("2. 删除 chroma_db 文件夹")
    print("3. 运行 build_vector_database.py 重新构建")
    print("4. 重启后端服务")

if __name__ == '__main__':
    rebuild_target_exercises()
