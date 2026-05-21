import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.retrieval.service import ResourceRetriever
from app.core.retrieval.retrieve_helpers.context import extract_query_context, ensure_collection_ready
from app.core.retrieval.retrieve_helpers.multi_theme import execute_multi_theme_retrieval

query = "分别找一下平面向量的坐标表示和复数的几何意义的教案"
print(f"测试查询: '{query}'")

# 创建检索器实例
retriever = ResourceRetriever()

# 提取查询上下文
query_context, early_result = extract_query_context(retriever, query, 0)
print(f"\n1. 查询上下文:")
print(f"   core_theme: {query_context['core_theme']}")
print(f"   core_themes: {query_context['core_themes']}")
print(f"   resource_types: {query_context.get('resource_types', [])}")

# 准备运行时上下文
retriever._current_query = query
retriever._current_quantity_limit = 500
retriever._current_query_features = {'original_query': query}

# 获取集合
collection, _ = ensure_collection_ready(retriever, query_context['core_theme'], query_context.get('board'))

# 处理主题
core_themes = query_context['core_themes']
if isinstance(core_themes[0], str) and "," in core_themes[0]:
    core_themes = [t.strip() for t in core_themes[0].split(",") if t.strip()]
print(f"\n2. 处理后的主题: {core_themes}")

# 检测是否分别查询
is_separate_query = any(keyword in query for keyword in ["分别", "各自", "分开"])
print(f"\n3. 是否分别查询: {is_separate_query}")

# 执行多主题检索
print("\n4. 执行多主题检索...")
results = execute_multi_theme_retrieval(
    retriever,
    collection,
    query,
    core_themes,
    500,
    ['教案'],
    query_context['question_type'],
)

print(f"\n5. 检索结果:")
print(f"   文档数量: {len(results.get('documents', [[]])[0]) if results.get('documents') else 0}")

# 打印最终结果中的主题分布
if results.get('metadatas') and results['metadatas'][0]:
    print(f"\n6. 结果中的主题分布:")
    theme_count = {}
    for meta in results['metadatas'][0]:
        matched_themes = meta.get('_matched_themes', [])
        for theme in matched_themes:
            theme_count[theme] = theme_count.get(theme, 0) + 1
    for theme, count in theme_count.items():
        print(f"   主题 '{theme}': {count} 个资源")

# 打印详细结果
if results.get('metadatas') and results['metadatas'][0]:
    print(f"\n7. 详细结果:")
    for i, meta in enumerate(results['metadatas'][0]):
        title = meta.get('title', '未知')
        matched_themes = meta.get('_matched_themes', [])
        print(f"   结果{i+1}: {title} (匹配主题: {matched_themes})")
