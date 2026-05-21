import chromadb
import sys
sys.path.insert(0, './app')

# 模拟语义门控的关键词提取和匹配逻辑
def _normalize_match_text(text):
    import re
    normalized = str(text or "").strip().lower()
    normalized = normalized.replace("的", "")
    normalized = re.sub(r"[\s,，。；;、:：()\[\]（）\-_/]+", "", normalized)
    return normalized

def _extract_theme_keywords(core_theme):
    keywords = []
    if isinstance(core_theme, str):
        themes = [t.strip() for t in core_theme.split(',') if t.strip()]
        for theme in themes:
            keywords.append(theme)
            import jieba
            jieba_keywords = list(jieba.cut(theme))
            keywords.extend([kw for kw in jieba_keywords if len(kw) > 1])
    return list(set(keywords))

# 连接到向量数据库
client = chromadb.PersistentClient(path='./chroma_db')
prob_coll = client.get_collection('math_resources_probability')

# 查询组合相关的课件
all_courseware = prob_coll.get(where={'resource_type': 'courseware'}, include=['metadatas'])

# 核心主题
core_theme = '组合数'
theme_keywords = _extract_theme_keywords(core_theme)
print("核心主题:", core_theme)
print("主题关键词:", theme_keywords)
print()

# 检查每个课件是否能通过语义门控
print("检查课件资源的关键词匹配情况:")
match_count = 0
no_match_count = 0
no_match_list = []

for meta in all_courseware['metadatas']:
    title = meta.get('title', '')
    content = meta.get('内容', '')
    teaching_use = meta.get('教学用途', '')
    source_file = meta.get('source_file', '')
    
    # 检查是否是练习课课件
    if teaching_use != '练习课课件':
        continue
    
    # 模拟语义门控的关键词匹配
    title_normalized = _normalize_match_text(title)
    content_normalized = _normalize_match_text(content)
    teaching_use_normalized = _normalize_match_text(teaching_use)
    
    # 检查关键词匹配
    matched = False
    for kw in theme_keywords:
        kw_normalized = _normalize_match_text(kw)
        if kw_normalized in title_normalized or kw_normalized in content_normalized:
            matched = True
            break
    
    if matched:
        match_count += 1
        print("匹配成功 - 标题:", title.encode('gbk', errors='ignore').decode('gbk'))
    else:
        no_match_count += 1
        no_match_list.append(title)

print()
print("匹配成功的练习课课件数量:", match_count)
print("未匹配的练习课课件数量:", no_match_count)
if no_match_list:
    print("未匹配的课件标题:")
    for title in no_match_list:
        print("  -", title.encode('gbk', errors='ignore').decode('gbk'))
