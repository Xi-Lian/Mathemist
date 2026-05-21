import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')

# 获取概率统计集合
try:
    prob_coll = client.get_collection('math_resources_probability')
    print("成功获取概率统计集合")
    
    # 查询课件资源
    results = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'], limit=20)
    
    print(f"\n找到 {len(results['metadatas'])} 条课件资源:")
    for i, meta in enumerate(results['metadatas'][:20]):
        print(f"\n资源 {i+1}:")
        print(f"  标题: {meta.get('title', '未知')}")
        print(f"  资源类型: {meta.get('resource_type', '未知')}")
        print(f"  教学用途: {meta.get('教学用途', '未知')}")
        print(f"  源文件: {meta.get('source_file', '未知')}")
        
    # 检查是否有练习课课件
    exercise_courseware = prob_coll.get(where={'教学用途': '练习课课件'}, include=['metadatas'], limit=10)
    print(f"\n找到 {len(exercise_courseware['metadatas'])} 条练习课课件:")
    for i, meta in enumerate(exercise_courseware['metadatas'][:10]):
        print(f"\n练习课课件 {i+1}:")
        print(f"  标题: {meta.get('title', '未知')}")
        print(f"  资源类型: {meta.get('resource_type', '未知')}")
        print(f"  教学用途: {meta.get('教学用途', '未知')}")
        
    # 检查是否有组合数相关的课件
    print("\n\n搜索包含'组合'的课件:")
    all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])
    combo_count = 0
    for meta in all_courseware['metadatas']:
        title = meta.get('title', '')
        content = meta.get('内容', '')
        teaching_use = meta.get('教学用途', '')
        if '组合' in title or '组合' in content:
            combo_count += 1
            if combo_count <= 10:
                print(f"\n组合相关课件 {combo_count}:")
                print(f"  标题: {title}")
                print(f"  内容: {content}")
                print(f"  教学用途: {teaching_use}")
    
    print(f"\n共找到 {combo_count} 条组合相关课件")
        
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
