import chromadb
import jieba

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 测试查询
query_text = "组合数的练习课课件"

# 查询课件资源
results = prob_coll.query(
    query_texts=[query_text],
    n_results=50,
    where={'resource_type': 'courseware'},
    include=['documents', 'metadatas', 'distances']
)

print("分析课件放宽逻辑的触发条件:")
print("=" * 80)

# 提取核心主题关键词（模拟代码中的逻辑）
core_theme = "组合数"
themes = [t.strip() for t in core_theme.split(',') if t.strip()]
theme_keywords = []
for theme in themes:
    theme_keywords.append(theme)
    jieba_keywords = list(jieba.cut(theme))
    theme_keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
theme_keywords = list(set(theme_keywords))
print(f"核心主题: '{core_theme}'")
print(f"主题关键词: {theme_keywords}")
print()

# 检查每个课件的条件
for i, meta in enumerate(results['metadatas'][0]):
    dist = results['distances'][0][i]
    title = meta.get('title', '')
    resource_type = meta.get('resource_type', '')
    teaching_use = meta.get('教学用途', '')
    
    # 检查课件资源识别条件
    is_courseware_resource = resource_type.lower() == 'courseware' or '课件' in teaching_use
    
    # 检查关键词匹配
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
    
    # 打印结果
    print(f"课件 {i+1}:")
    print(f"  标题: {title}")
    print(f"  距离: {dist:.4f}")
    print(f"  resource_type: '{resource_type}'")
    print(f"  教学用途: '{teaching_use}'")
    print(f"  is_courseware_resource: {is_courseware_resource}")
    print(f"  distance <= 1.0: {dist <= 1.0}")
    print(f"  关键词匹配: {kw_matched} (匹配关键词: {matched_kw})")
    
    # 判断是否应该通过
    should_pass = is_courseware_resource and dist <= 1.0 and kw_matched
    print(f"  课件放宽逻辑是否应该通过: {should_pass}")
    print()
    
    # 特别检查组合数相关课件
    if '组合' in title:
        print("  ⚠️ 这是组合数相关课件！")
        print()
