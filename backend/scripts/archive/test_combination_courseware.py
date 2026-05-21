import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 查询所有组合相关的课件
all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas', 'documents'])

print("找到所有组合相关的练习课课件:")
combo_exercise_courseware = []
for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    content = meta.get('内容', '')
    teaching_use = meta.get('教学用途', '')
    
    if teaching_use == '练习课课件' and ('组合' in title or '组合' in content):
        combo_exercise_courseware.append({
            'title': title,
            'content': content,
            'teaching_use': teaching_use
        })

print(f"共找到 {len(combo_exercise_courseware)} 条组合相关练习课课件:")
for i, c in enumerate(combo_exercise_courseware):
    print(f"\n{i+1}. 标题: {c['title']}")
    print(f"   内容: {c['content']}")
    print(f"   教学用途: {c['teaching_use']}")

# 现在测试这些课件的向量相似度
print("\n\n测试组合数练习课课件的向量相似度:")
query_text = "组合数 练习课 课件"

# 获取这些课件的ID
combo_ids = []
for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '')
    if teaching_use == '练习课课件' and '组合' in title:
        combo_ids.append(all_courseware['ids'][i])

print(f"\n组合数练习课课件的ID: {combo_ids}")

# 查询这些课件的相似度
results = prob_coll.query(
    query_texts=[query_text],
    n_results=30,
    where={'resource_type': 'courseware'},
    include=['documents', 'metadatas', 'distances']
)

print("\n检索结果中组合相关练习课课件:")
found_count = 0
for i, meta in enumerate(results['metadatas'][0]):
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '')
    dist = results['distances'][0][i]
    
    if teaching_use == '练习课课件' and '组合' in title:
        found_count += 1
        print(f"✅ 找到: distance={dist:.4f}, 标题={title}")

print(f"\n共找到 {found_count} 条组合数练习课课件")
