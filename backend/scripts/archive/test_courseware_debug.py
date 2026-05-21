import sys
import os
sys.path.insert(0, 'app')

# 设置环境变量
os.environ["APP_VERBOSE_LOGS"] = "1"

from core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder()
client = builder.get_chroma_client()

# 检查概率统计板块的集合
try:
    collection = client.get_collection('math_resources_probability')
    print('概率统计板块资源数量:', collection.count())
    
    # 获取所有资源
    results = collection.get(where={}, limit=150)
    
    # 统计资源类型分布
    type_counts = {}
    courseware_details = []
    
    for i, meta in enumerate(results['metadatas']):
        resource_type = meta.get('resource_type', 'unknown')
        title = meta.get('title', '')
        teaching_use = meta.get('教学用途', '')
        source_file = meta.get('source_file', '')
        
        type_counts[resource_type] = type_counts.get(resource_type, 0) + 1
        
        # 收集课件资源的详细信息
        if resource_type == 'courseware':
            courseware_details.append({
                'title': title,
                'teaching_use': teaching_use,
                'source_file': source_file,
                'metadata': meta
            })
    
    print('\n资源类型分布:')
    for resource_type, count in type_counts.items():
        print(f'  {resource_type}: {count}条')
    
    print(f'\n课件资源数量: {len(courseware_details)}')
    print('课件资源详情:')
    for c in courseware_details[:10]:
        print(f"  - 标题: {c['title'][:50]}")
        print(f"    教学用途: {c['teaching_use']}")
        print(f"    源文件: {c['source_file'][:60]}")
        print()
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
