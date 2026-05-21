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
        print()
        print('=' * 60)
        print('课件', combo_count)
        print('标题:', title)
        print('教学用途:', teaching_use)
        print('内容长度:', len(content), '字符')
        print('内容:', repr(content))
        print()

# 检查查询词与课件的匹配
print()
print('分析查询词与课件的匹配:')
query_text = '组合数的练习课课件'
print('查询词:', query_text)

for i, meta in enumerate(all_courseware['metadatas']):
    title = meta.get('title', '')
    content = meta.get('内容', '')
    teaching_use = meta.get('教学用途', '')
    
    if teaching_use == '练习课课件' and '组合' in title:
        print()
        print('标题:', title)
        match_count = 0
        if '组合数' in title:
            match_count += 1
            print('  组合数: 在标题中')
        if '练习课' in teaching_use:
            match_count += 1
            print('  练习课: 在教学用途中')
        if '课件' in teaching_use:
            match_count += 1
            print('  课件: 在教学用途中')
        print('  匹配关键词数:', match_count)
