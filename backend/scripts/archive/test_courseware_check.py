import sys
sys.path.insert(0, 'app')

from core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder()
client = builder.get_chroma_client()

# 检查概率统计板块的集合
try:
    collection = client.get_collection('math_resources_probability')
    print('概率统计板块资源数量:', collection.count())
    
    results = collection.get(where={}, limit=100)
    
    courseware_count = 0
    exercise_courseware_count = 0
    combination_courseware = []
    
    for i, meta in enumerate(results['metadatas']):
        resource_type = meta.get('resource_type', 'unknown')
        title = meta.get('title', '')
        teaching_use = meta.get('教学用途', '')
        source_file = meta.get('source_file', '')
        
        if resource_type == 'courseware':
            courseware_count += 1
            if '练习课' in teaching_use or '练习' in teaching_use:
                exercise_courseware_count += 1
            if '组合数' in title or '组合' in title:
                combination_courseware.append({
                    'title': title,
                    'teaching_use': teaching_use,
                    'source_file': source_file
                })
    
    print(f'课件资源数量: {courseware_count}')
    print(f'练习课课件数量: {exercise_courseware_count}')
    print(f'组合数相关课件: {len(combination_courseware)}')
    for c in combination_courseware[:10]:
        print(f"  - {c['title']} | 教学用途: {c['teaching_use']}")
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
