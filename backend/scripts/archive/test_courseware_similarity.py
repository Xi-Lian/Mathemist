import chromadb
import os

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'chroma_db')

try:
    client = chromadb.PersistentClient(path=db_path)
    
    # 获取概率统计板块集合
    collection = client.get_collection('math_resources_probability')
    
    # 查询与"组合数 练习课 课件"相关的课件资源
    query_text = "组合数 练习课 课件"
    print(f"查询文本: {query_text}")
    
    # 只查询课件类型的资源
    results = collection.query(
        query_texts=[query_text],
        where={"resource_type": "courseware"},
        n_results=20,
        include=['metadatas', 'distances']
    )
    
    print(f"\n检索到的课件资源数量: {len(results['ids'][0])}")
    
    if len(results['ids'][0]) > 0:
        print("\n课件资源检索结果（按相似度排序）:")
        for i, (id_val, meta, dist) in enumerate(zip(results['ids'][0], results['metadatas'][0], results['distances'][0])):
            title = meta.get('title', '').encode('gbk', errors='ignore').decode('gbk')
            teaching_use = meta.get('教学用途', '').encode('gbk', errors='ignore').decode('gbk')
            print(f"\n  {i+1}. ID: {id_val}")
            print(f"     标题: {title}")
            print(f"     教学用途: {teaching_use}")
            print(f"     相似度距离: {dist:.4f}")
            
except Exception as e:
    print(f'错误: {e}')
    import traceback
    traceback.print_exc()
