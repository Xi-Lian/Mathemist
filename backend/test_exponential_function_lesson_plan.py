from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor
from app.core.intent_analyzer import IntentAnalyzer

# 初始化组件
retriever = ResourceRetriever()
preprocessor = QueryPreprocessor()
analyzer = IntentAnalyzer()

# 测试搜索"推送指数函数的概念教案"
query = "推送指数函数的概念教案"

print(f"搜索查询: {query}")
print()

# 意图理解
intent_result = analyzer.analyze(query)
print(f"意图分析结果:")
print(f"  主要意图: {intent_result.get('intent', '')}")
print(f"  用户需求: {intent_result.get('user_needs', '')}")
print(f"  资源类型: {intent_result.get('resource_types', [])}")
print()

# 检索资源
results = retriever.retrieve(
    query,
    intent_result.get('intent', 'search'),
    resource_types=intent_result.get('resource_types', [])
)

print(f"检索结果:")
print(f"  教案: {len(results.get('lesson_plan_patterns', []))}条")
print(f"  习题: {len(results.get('exercise_resources', []))}条")
print(f"  课件: {len(results.get('courseware_resources', []))}条")
print(f"  教学大纲: {len(results.get('syllabus_resources', []))}条")
print()

# 打印前10个教案资源
print("前10个教案资源:")
for i, item in enumerate(results.get('lesson_plan_patterns', [])[:10]):
    print(f"{i+1}. {item.get('title', '')} - 相似度: {item.get('relevance', 0):.1%}, 主题匹配: {item.get('theme_match', False)}, source: {item.get('source', '')}")
