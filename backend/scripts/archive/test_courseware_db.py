import sys
import os
sys.path.insert(0, 'app')

from core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder()
client = builder.get_chroma_client()

try:
    collection = client.get_collection('math_resources_probability')
    print('概率统计板块资源数量:', collection.count())
    
    results = collection.get(where={}, limit=150)
    
    print('\n=== 检查资源类型分布 ===')
    type_counts = {}
    for meta in results['metadatas']:
        resource_type = meta.get('resource_type', 'unknown')
        type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
    
    for resource_type, count in type_counts.items():
        print(f'  {resource_type}: {count}条')
    
    print('\n=== 检查课件资源的教学用途字段 ===')
    courseware_with_teaching_use = 0
    courseware_without_teaching_use = 0
    
    for meta in results['metadatas']:
        resource_type = meta.get('resource_type', 'unknown')
        teaching_use = meta.get('教学用途', '')
        
        if resource_type == 'courseware':
            if teaching_use:
                courseware_with_teaching_use += 1
                if '练习课' in teaching_use or '练习' in teaching_use:
                    print(f"  ✓ 课件: {meta.get('title', '')[:40]} | 教学用途: {teaching_use}")
            else:
                courseware_without_teaching_use += 1
    
    print(f'\n  有教学用途的课件: {courseware_with_teaching_use}')
    print(f'  无教学用途的课件: {courseware_without_teaching_use}')
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
