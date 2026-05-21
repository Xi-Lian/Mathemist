import json
import os

# 检查几何板块的向量数据库文件
vector_db_path = os.path.join('app', 'data', 'vector_db', 'math_resources_geometry.json')

if os.path.exists(vector_db_path):
    with open(vector_db_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"几何板块总资源数: {len(data)}")
    
    # 查找包含"平面"的资源
    plane_resources = []
    for item in data:
        title = item.get('title', '')
        content = item.get('content', '')
        if '平面' in title or '平面' in content:
            plane_resources.append({
                'title': title,
                'file_type': item.get('file_type', ''),
                'content_length': len(content)
            })
    
    print(f"包含'平面'的资源数: {len(plane_resources)}")
    
    if plane_resources:
        print("\n前10个包含'平面'的资源:")
        for i, res in enumerate(plane_resources[:10]):
            print(f"{i+1}. {res['title']} ({res['file_type']})")
else:
    print(f"向量数据库文件不存在: {vector_db_path}")