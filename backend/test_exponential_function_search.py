from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor
from app.core.theme_matcher import ThemeMatcher
import json

# 初始化组件
retriever = ResourceRetriever()
preprocessor = QueryPreprocessor()
theme_matcher = ThemeMatcher()

# 测试搜索"指数函数的资料"
query = "指数函数的资料"

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

# 打印前10个习题资源
print("前10个习题资源:")
for i, item in enumerate(results.get('exercise_resources', [])[:10]):
    print(f"{i+1}. {item.get('source_file', '')} - 相似度: {item.get('similarity', 0):.1f}%, 主题匹配: {item.get('theme_matched', False)}")
