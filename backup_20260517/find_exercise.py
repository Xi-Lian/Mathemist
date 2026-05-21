#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
sys.path.append('d:\\Git_Repository\\Mathemist\\backend')

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    builder = VectorDatabaseBuilder('learning_resource')
    client = builder.get_chroma_client()
    
    # 检查所有集合中的exercise资源
    collections = ['math_resources_function', 'math_resources_geometry', 
                   'math_resources_probability', 'math_resources_algebra']
    
    for col_name in collections:
        try:
            col = client.get_collection(col_name)
            # 过滤exercise类型
            res = col.get(where={'resource_type': 'exercise'}, limit=1, include=['metadatas'])
            
            if res and res.get('metadatas'):
                meta = res['metadatas'][0]
                print("Exercise Metadata Structure from", col_name)
                print("=" * 50)
                for key, value in meta.items():
                    if isinstance(value, str):
                        if len(value) > 80:
                            value = value[:80] + "..."
                    print("%s: %s" % (key, value))
                
                # 检查图片字段
                print("\nImage fields found:")
                has_image = False
                for key, value in meta.items():
                    if isinstance(value, str) and (value.endswith('.png') or value.endswith('.jpg')):
                        print("  %s = %s" % (key, value))
                        has_image = True
                if not has_image:
                    print("  No image fields found")
                print()
                break
        except Exception as e:
            pass

if __name__ == "__main__":
    main()