#!/usr/bin/env python3
import sys
sys.path.insert(0, 'd:/Git_Repository/Mathemist/backend')

import chromadb
import jieba

print("=" * 60)
print("完整检索流程测试")
print("=" * 60)

# 1. 连接数据库
print("\n1. 连接数据库...")
client = chromadb.PersistentClient(path='backend/chroma_db')

# 2. 获取集合
print("\n2. 获取集合...")
collections = client.list_collections()
print(f"数据库中的集合: {[col.name for col in collections]}")

collection = None
for col in collections:
    if 'probability' in col.name.lower():
        collection = client.get_collection(col.name)
        print(f"使用集合: {col.name}")
        break

if not collection:
    print("错误: 找不到概率统计板块集合")
    sys.exit(1)

# 3. 查询所有courseware资源
print("\n3. 查询所有courseware资源...")
results = collection.get(
    where={'resource_type': 'courseware'},
    include=['documents', 'metadatas']
)
print(f"数据库中courseware总数: {len(results['documents'])}")

# 4. 测试精确匹配
print("\n4. 测试精确匹配...")
core_theme = '分类加法计数原理'
themes = core_theme.split(',')
themes = [theme.strip() for theme in themes if theme.strip()]

# jieba分词
core_theme_keywords = []
for theme in themes:
    theme_keywords = list(jieba.cut(theme))
    theme_keywords = [kw for kw in theme_keywords if len(kw) > 1]
    core_theme_keywords.extend(theme_keywords)
core_theme_keywords = list(set(core_theme_keywords))
print(f"核心主题: {themes}")
print(f"关键词: {core_theme_keywords}")

# 精确匹配
matched = []
for meta in results['metadatas']:
    title = meta.get('title', '')
    teaching_use = meta.get('教学用途', '') or ''
    haystack = f'{title} {teaching_use}'

    match_found = False
    for theme in themes:
        if theme in haystack:
            match_found = True
            break

    if not match_found:
        for keyword in core_theme_keywords:
            if keyword in haystack:
                match_found = True
                break

    if match_found:
        matched.append(meta)

print(f"\n精确匹配总数: {len(matched)}")

# 5. 检查教学用途
print("\n5. 检查匹配结果的教学用途...")
practice_count = 0
for meta in matched:
    title = meta.get('title', '')[:40]
    teaching_use = meta.get('教学用途', '')
    if '练习课' in teaching_use:
        practice_count += 1
        print(f"✓ 练习课: {title}...")
        print(f"  教学用途: {teaching_use}")

print(f"\n包含'练习课'的数量: {practice_count}")

# 6. 测试resource_type匹配
print("\n6. 测试resource_type匹配...")
from app.core.retrieval.classify_results_helpers.resource_type import matches_requested_resource_type, normalize_resource_type

resource_types = ['课件']
matched_with_type = 0

for meta in matched:
    resource_type = normalize_resource_type(meta, meta.get('resource_type', 'theory'))
    is_matched = matches_requested_resource_type(resource_type, resource_types)
    print(f"  title: {meta.get('title', '')[:30]}...")
    print(f"  resource_type: {resource_type}, matched: {is_matched}")
    if is_matched:
        matched_with_type += 1

print(f"\n通过resource_type匹配的数量: {matched_with_type}")

print("\n" + "=" * 60)
print("结论:")
if practice_count > 0 and matched_with_type > 0:
    print("✓ 精确匹配能找到结果，resource_type也匹配")
elif practice_count > 0:
    print("✗ 精确匹配能找到练习课课件，但resource_type不匹配")
else:
    print("✗ 精确匹配找不到练习课课件")
print("=" * 60)