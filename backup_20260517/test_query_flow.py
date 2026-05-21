import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置输出编码
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'chroma_db')
print(f"数据库路径: {db_path}")

# 模拟查询
query = "找一下关于分类加法计数原理的练习课课件"
core_theme = "分类加法计数原理"
resource_types = ["习题", "课件"]

print("=" * 100)
print(f"模拟查询: {query}")
print(f"核心主题: {core_theme}")
print(f"资源类型: {resource_types}")
print("=" * 100)

# 连接数据库
client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection('math_resources_probability')

# 第一步：先获取所有课件，看看有哪些练习课课件
print("\n【步骤1】获取所有课件资源...")
all_courseware = collection.get(
    where={"resource_type": "courseware"},
    include=["documents", "metadatas"]
)
print(f"总课件数: {len(all_courseware['documents'])}")

practice_courseware = []
for doc, meta in zip(all_courseware["documents"], all_courseware["metadatas"]):
    teaching_use = meta.get("教学用途", "")
    if "练习课" in teaching_use:
        practice_courseware.append((doc, meta))

print(f"练习课课件数: {len(practice_courseware)}")
print("\n练习课课件列表:")
for i, (doc, meta) in enumerate(practice_courseware):
    print(f"{i+1}. {meta.get('title', '')} | {meta.get('教学用途', '')}")

# 第二步：模拟课件精确匹配
print("\n【步骤2】模拟课件精确匹配...")
print(f"核心主题: '{core_theme}'")

# 模拟课件精确匹配逻辑
exact_match_where = {"resource_type": "courseware"}
exact_match_results = collection.get(
    where=exact_match_where,
    include=["documents", "metadatas"]
)
print(f"ChromaDB返回原始课件数: {len(exact_match_results['documents'])}")

# 提取核心主题关键词
import jieba
core_theme_keywords = []
themes = core_theme.split(',') if isinstance(core_theme, str) else core_theme
themes = [theme.strip() for theme in themes if theme.strip()]

for theme in themes:
    theme_keywords = list(jieba.cut(theme))
    theme_keywords = [kw for kw in theme_keywords if len(kw) > 1]
    core_theme_keywords.extend(theme_keywords)
core_theme_keywords = list(set(core_theme_keywords))
print(f"核心主题关键词: {core_theme_keywords}")

# 过滤
filtered_docs = []
filtered_metas = []

for doc, meta in zip(exact_match_results["documents"], exact_match_results["metadatas"]):
    title = meta.get("title", "") or ""
    teaching_use = meta.get("教学用途", "") or ""
    haystack = f"{title} {teaching_use}"
    
    # 只检查包含"分类"或"计数"的课件
    if "分类" not in title and "计数" not in title:
        continue
    
    print(f"\n检查: title='{title}', teaching_use='{teaching_use}'")
    print(f"haystack: '{haystack}'")
    
    match_found = False
    
    # 检查主题
    for theme in themes:
        if theme in haystack:
            print(f"  [OK] 主题匹配: '{theme}'")
            match_found = True
            break
    
    # 检查关键词
    if not match_found:
        for keyword in core_theme_keywords:
            if keyword in haystack:
                print(f"  [OK] 关键词匹配: '{keyword}'")
                match_found = True
                break
    
    if match_found:
        filtered_docs.append(doc)
        filtered_metas.append(meta)
        print(f"  [+] 保留此课件")
    else:
        print(f"  [-] 过滤此课件")

print(f"\n精确匹配后找到: {len(filtered_docs)} 条结果")
if filtered_metas:
    print("\n匹配结果:")
    for i, meta in enumerate(filtered_metas):
        print(f"{i+1}. {meta.get('title', '')} | {meta.get('教学用途', '')}")
