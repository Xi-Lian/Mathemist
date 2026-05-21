import chromadb
import jieba

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 查询所有课件资源
all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])

# 找出所有组合数练习课课件
combo_courseware = []
for meta in all_courseware['metadatas']:
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '')
    if teaching_use == '练习课课件' and '组合' in title:
        combo_courseware.append(meta)

print("找到的组合数练习课课件:")
print("=" * 80)
for meta in combo_courseware:
    print(f"标题: {meta.get('title', '')}")
    print(f"教学用途: {meta.get('教学用途', '')}")
    print(f"内容: {meta.get('内容', '')}")
    print()

# 测试这些课件的向量相似度
query_text = "组合数的练习课课件"
print("\n测试组合数练习课课件的向量相似度:")
print("=" * 80)

# 获取这些课件的标题列表
combo_titles = [meta.get('title', '') for meta in combo_courseware]

# 查询所有课件
results = prob_coll.query(
    query_texts=[query_text],
    n_results=50,
    where={'resource_type': 'courseware'},
    include=['documents', 'metadatas', 'distances']
)

# 找出组合数课件的结果
print("组合数练习课课件在检索结果中的情况:")
found_count = 0
for i, meta in enumerate(results['metadatas'][0]):
    title = meta.get('title', '')
    dist = results['distances'][0][i]
    resource_type = meta.get('resource_type', '')
    teaching_use = meta.get('教学用途', '')
    
    if title in combo_titles:
        found_count += 1
        print(f"\n找到组合数练习课课件 {found_count}:")
        print(f"  标题: {title}")
        print(f"  距离: {dist:.4f}")
        print(f"  resource_type: '{resource_type}'")
        print(f"  教学用途: '{teaching_use}'")
        
        # 检查课件放宽逻辑条件
        is_courseware_resource = resource_type.lower() == 'courseware' or '课件' in teaching_use
        print(f"  is_courseware_resource: {is_courseware_resource}")
        print(f"  distance <= 1.0: {dist <= 1.0}")
        
        # 检查关键词匹配
        core_theme = "组合数"
        themes = [t.strip() for t in core_theme.split(',') if t.strip()]
        theme_keywords = []
        for theme in themes:
            theme_keywords.append(theme)
            jieba_keywords = list(jieba.cut(theme))
            theme_keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
        theme_keywords = list(set(theme_keywords))
        
        title_normalized = title.strip().lower().replace("的", "").replace(" ", "").replace("\t", "")
        teaching_use_normalized = teaching_use.strip().lower().replace("的", "").replace(" ", "").replace("\t", "")
        
        kw_matched = False
        matched_kw = None
        for kw in theme_keywords:
            kw_normalized = kw.strip().lower().replace("的", "").replace(" ", "").replace("\t", "")
            if kw_normalized in title_normalized or kw_normalized in teaching_use_normalized:
                kw_matched = True
                matched_kw = kw
                break
        
        print(f"  主题关键词: {theme_keywords}")
        print(f"  关键词匹配: {kw_matched} (匹配关键词: {matched_kw})")
        
        should_pass = is_courseware_resource and dist <= 1.0 and kw_matched
        print(f"  课件放宽逻辑是否应该通过: {should_pass}")

print(f"\n共找到 {found_count} 条组合数练习课课件")
print(f"未找到的组合数练习课课件: {set(combo_titles) - {r['title'] for r in results['metadatas'][0]}}")
