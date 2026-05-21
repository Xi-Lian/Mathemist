import chromadb
from chromadb.config import Settings
from pathlib import Path

# 获取ChromaDB客户端
db_path = Path(__file__).parent / 'chroma_db'
client = chromadb.PersistentClient(
    path=str(db_path),
    settings=Settings(
        anonymized_telemetry=False,
        allow_reset=True
    )
)

# 检查几何板块集合
try:
    collection = client.get_collection(name="math_resources_geometry")
    print("几何板块集合存在")
    
    # 获取集合中的所有资源
    results = collection.get(include=['metadatas'])
    total_resources = len(results['metadatas'])
    print(f"几何板块总资源数: {total_resources}")
    
    # 统计资源类型分布
    type_stats = {}
    plane_resources = []
    plane_lesson_plans = []
    
    for i, metadata in enumerate(results['metadatas']):
        try:
            resource_type = metadata.get('resource_type', 'unknown')
            type_stats[resource_type] = type_stats.get(resource_type, 0) + 1
            
            # 检查包含'平面'的资源
            title = metadata.get('title', '')
            if '平面' in title:
                plane_resources.append({
                    'title': title,
                    'resource_type': resource_type
                })
                
                if resource_type == 'lesson_plan':
                    plane_lesson_plans.append(title)
        except Exception as e:
            # 跳过编码错误的资源
            pass
    
    print(f"\n资源类型分布:")
    for rtype, count in type_stats.items():
        try:
            print(f"{rtype}: {count}")
        except Exception as e:
            print(f"[类型包含特殊字符]: {count}")
    
    print(f"\n包含'平面'的资源数: {len(plane_resources)}")
    print(f"包含'平面'的lesson_plan资源数: {len(plane_lesson_plans)}")
    
    if plane_lesson_plans:
        print("\n前10个包含'平面'的lesson_plan资源:")
        for i, title in enumerate(plane_lesson_plans[:10]):
            try:
                print(f"{i+1}. {title}")
            except Exception as e:
                print(f"{i+1}. [标题包含特殊字符]")
    else:
        print("\n未找到包含'平面'的lesson_plan资源")
        
        # 打印前10个包含'平面'的资源，看看它们的资源类型
        if plane_resources:
            print("\n前10个包含'平面'的资源:")
            for i, res in enumerate(plane_resources[:10]):
                try:
                    print(f"{i+1}. {res['title']} ({res['resource_type']})")
                except Exception as e:
                    print(f"{i+1}. [标题包含特殊字符] ({res['resource_type']})")

except Exception as e:
    print(f"检查几何板块集合失败: {str(e)}")
