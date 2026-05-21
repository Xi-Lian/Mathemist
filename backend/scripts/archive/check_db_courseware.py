import chromadb
import os

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'chroma_db')
print(f"数据库路径: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    
    # 检查概率统计板块集合
    collection = client.get_collection('math_resources_probability')
    print('概率统计板块资源数量:', collection.count())
    
    # 查询所有课件资源
    results = collection.get(where={"resource_type": "courseware"}, include=['metadatas'])
    
    print(f'\n课件资源数量: {len(results["metadatas"])}')
    
    if len(results["metadatas"]) > 0:
        print('\n课件资源示例:')
        for i, meta in enumerate(results["metadatas"][:5]):
            title = meta.get('title', '').encode('gbk', errors='ignore').decode('gbk')
            teaching_use = meta.get('教学用途', '').encode('gbk', errors='ignore').decode('gbk')
            print(f"\n  {i+1}. 标题: {title}")
            print(f"     教学用途: {teaching_use}")
    
    # 检查是否有组合数相关的课件
    all_results = collection.get(include=['metadatas'])
    combination_count = 0
    exercise_count = 0
    
    for meta in all_results["metadatas"]:
        title = meta.get('title', '')
        teaching_use = meta.get('教学用途', '')
        resource_type = meta.get('resource_type', '')
        
        if resource_type == 'courseware':
            if '组合数' in title:
                combination_count += 1
            if '练习课' in teaching_use:
                exercise_count += 1
    
    print(f'\n组合数相关课件数量: {combination_count}')
    print(f'练习课课件数量: {exercise_count}')
        
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
