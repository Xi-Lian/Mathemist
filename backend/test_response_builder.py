from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor
from app.core.response_builder import ResponseBuilder
from app.core.model_config import ModelConfig

# 初始化组件
retriever = ResourceRetriever()
preprocessor = QueryPreprocessor()
response_builder = ResponseBuilder()

# 测试搜索"给我指数函数的资料"
query = "给我指数函数的资料"

print(f"搜索查询: {query}")
print()

# 预处理查询
processed_query = preprocessor.preprocess(query)

print(f"预处理结果:")
print(f"  原始查询: {processed_query.get('original_query', '')}")
print(f"  主题: {processed_query.get('intent', {}).get('topic', '')}")
print(f"  资源类型: {processed_query.get('intent', {}).get('resource_types', [])}")
print()

# 检索资源
results = retriever.retrieve(query)

print(f"检索结果:")
print(f"  教案: {len(results.get('lesson_plan_patterns', []))}条")
print(f"  习题: {len(results.get('exercise_resources', []))}条")
print(f"  课件: {len(results.get('courseware_resources', []))}条")
print(f"  教学大纲: {len(results.get('syllabus_resources', []))}条")
print()

# 构建响应
state = {
    "user_needs": query,
    "resource_types": processed_query.get('intent', {}).get('resource_types', []),
    "retrieved_resources": results
}

response = response_builder._format_resources(state)

print("响应内容:")
print(response)
