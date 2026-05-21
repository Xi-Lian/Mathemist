#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
重建向量数据库索引
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def build_database():
    """重建向量数据库"""
    print("=" * 60)
    print("开始重建向量数据库索引")
    print("=" * 60)
    
    try:
        from app.core.vector_database_builder import VectorDatabaseBuilder
        
        learning_resource_path = r"D:\Git_Repository\Mathemist\learning_resource"
        builder = VectorDatabaseBuilder(learning_resource_path)
        
        print("\n1. 开始构建向量数据库...")
        success = builder.build_vector_database(force_rebuild=True)
        
        if success:
            print("   索引构建完成")
            
            print("\n2. 验证索引...")
            from chromadb import Client
            client = builder.get_chroma_client()
            
            collections = client.list_collections()
            print("   数据库中的集合:")
            for col in collections:
                print("     -", col.name, "(", col.count(), "条记录)")
            
            print("\n" + "=" * 60)
            print("索引重建完成！")
            print("=" * 60)
        else:
            print("索引构建失败")
            
    except Exception as e:
        print("索引重建失败:", str(e)[:200])
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    build_database()