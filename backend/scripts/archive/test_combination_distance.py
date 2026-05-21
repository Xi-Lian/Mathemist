import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 查询所有课件资源的相似度
query_text = "组合数 练习课 课件"

# 获取所有课件资源
all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])

# 记录组合相关课件的信息
combo_info = {}
for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '')
    if teaching_use == '练习课课件' and '组合' in title:
        combo_info[title] = {
            'title': title,
            'teaching_use': teaching_use
        }

print("组合数练习课课件列表:")
for title, info in combo_info.items():
    print(f"  - {title}")

# 执行向量检索，获取更多结果
results = prob_coll.query(
    query_texts=[query_text],
    n_results=50,  # 获取更多结果
    where={'resource_type': 'courseware'},
    include=['documents', 'metadatas', 'distances']
)

print(f"\n检索到 {len(results['documents'][0])} 条课件资源")
print("\n检索结果中的组合数练习课课件:")
found_in_results = []

for i, meta in enumerate(results['metadatas'][0]):
    dist = results['distances'][0][i]
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '')
    
    if title in combo_info:
        found_in_results.append(title)
        print(f"标题: {title}")
        print(f"  distance: {dist:.4f}")
        print(f"  教学用途: {teaching_use}")
        print()

print(f"\n在检索结果中找到 {len(found_in_results)} 条组合数练习课课件")
print(f"未找到的组合数练习课课件: {set(combo_info.keys()) - set(found_in_results)}")

# 打印所有检索结果的前20条
print("\n\n前20条检索结果:")
for i in range(min(20, len(results['documents'][0]))):
    dist = results['distances'][0][i]
    title = results['metadatas'][0][i].get('title', '未知')
    teaching_use = results['metadatas'][0][i].get('教学用途', '未知')
    print(f"{i+1}. distance={dist:.4f}, 标题={title[:50]}, 教学用途={teaching_use}")
