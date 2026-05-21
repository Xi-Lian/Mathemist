import chromadb

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 查询所有组合相关的练习课课件
all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas', 'documents'])

print("分析组合数练习课课件的内容:")
combo_count = 0
for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    content = meta.get('内容', '')
    teaching_use = meta.get('教学用途', '')
    
    if teaching_use == '练习课课件' and '组合' in title:
        combo_count += 1
        print(f"\n{'='*60}")
        print(f"课件 {combo_count}:")
        print(f"标题: {title}")
        print(f"教学用途: {teaching_use}")
        print(f"内容长度: {len(content)} 字符")
        print(f"内容前200字符: '{content[:200]}...'")
        
        # 检查内容中是否包含关键词
        keywords = ['组合', '组合数', '排列', '计数']
        print("\n关键词匹配情况:")
        for kw in keywords:
            if kw in content:
                print(f"  ✅ '{kw}' 在内容中出现")
            else:
                print(f"  ❌ '{kw}' 不在内容中")

# 检查查询词与课件内容的匹配
print("\n\n分析查询词与课件内容的匹配:")
query_text = "组合数的练习课课件"
query_keywords = ['组合数', '练习课', '课件']

for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    content = meta.get('内容', '')
    teaching_use = meta.get('教学用途', '')
    
    if teaching_use == '练习课课件' and '组合' in title:
        print(f"\n标题: {title}")
        print("查询关键词匹配:")
        for kw in query_keywords:
            if kw in title:
                print(f"  ✅ '{kw}' 在标题中")
            elif kw in content:
                print(f"  ✅ '{kw}' 在内容中")
            elif kw in teaching_use:
                print(f"  ✅ '{kw}' 在教学用途中")
            else:
                print(f"  ❌ '{kw}' 未匹配")
