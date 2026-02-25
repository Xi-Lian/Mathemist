from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor
from app.core.theme_matcher import ThemeMatcher

# 初始化组件
retriever = ResourceRetriever()
preprocessor = QueryPreprocessor()
theme_matcher = ThemeMatcher()

# 测试搜索"我想要对数函数和幂函数的习题"
query = "我想要对数函数和幂函数的习题"

print(f"搜索查询: {query}")
print()

# 预处理查询
processed_query = preprocessor.preprocess(query)
print(f"预处理后的查询: {processed_query}")
print()

# 检索资源
results = retriever.retrieve(query)

print(f"检索结果:")
print(f"  教案: {len(results.get('lesson_plan_patterns', []))}条")
print(f"  习题: {len(results.get('exercise_resources', []))}条")
print(f"  课件: {len(results.get('courseware_resources', []))}条")
print(f"  教学大纲: {len(results.get('syllabus_resources', []))}条")
print()

# 打印前20个习题资源
print("前20个习题资源:")
for i, item in enumerate(results.get('exercise_resources', [])[:20]):
    print(f"{i+1}. {item.get('title', '')} - 相似度: {item.get('relevance', 0):.1%}, 主题匹配: {item.get('theme_match', False)}, source: {item.get('source', '')}")
