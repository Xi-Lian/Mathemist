#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    builder = VectorDatabaseBuilder('learning_resource')
    client = builder.get_chroma_client()
    
    # 获取函数板块集合
    col = client.get_collection('math_resources_function')
    
    # 获取一条数据
    res = col.get(limit=1, include=['metadatas'])
    
    if res and res.get('metadatas'):
        meta = res['metadatas'][0]
        print("Exercise Metadata Structure:")
        print("=" * 50)
        for key, value in meta.items():
            if isinstance(value, str):
                if len(value) > 50:
                    value = value[:50] + "..."
            print(f"{key}: {value}")
        
        # 检查是否有图片相关字段
        print("\nChecking for image fields:")
        for key, value in meta.items():
            if isinstance(value, str) and (value.endswith('.png') or value.endswith('.jpg')):
                print(f"Found image: {key} = {value}")

if __name__ == "__main__":
    main()