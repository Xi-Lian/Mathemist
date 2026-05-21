import chromadb
import os
import sys

# 设置输出编码为UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'chroma_db')
print(f"数据库路径: {db_path}")

try:
    client = chromadb.PersistentClient(path=db_path)
    
    # 检查概率统计板块集合
    collection = client.get_collection('math_resources_probability')
    print('概率统计板块资源数量:', collection.count())
    
    # 查询所有课件资源
    results = collection.get(where={"resource_type": "courseware"}, include=['metadatas', 'documents'])
    
    print(f'\n课件资源数量: {len(results["metadatas"])}')
    
    # 检查是否有分类加法计数原理相关的课件
    found = False
    for i, meta in enumerate(results["metadatas"]):
        title = meta.get('title', '')
        teaching_use = meta.get('教学用途', '')
        doc = results["documents"][i] if i < len(results["documents"]) else ''
        
        if '分类加法计数原理' in title or '分类加法计数原理' in doc or '6.1' in title:
            print(f"\nFound relevant courseware:")
            print(f"  Title: {title}")
            print(f"  Teaching use: {teaching_use}")
            print(f"  Document content: {doc[:100]}...")
            found = True
    
    if not found:
        print(f'\nNot found classification courseware')
        print(f'\nAll practice courseware:')
        for i, meta in enumerate(results["metadatas"]):
            title = meta.get('title', '')
            teaching_use = meta.get('教学用途', '')
            if '练习课' in teaching_use:
                print(f"  - {title} ({teaching_use})")
        
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
