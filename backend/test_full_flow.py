from app.core.resource_retriever import ResourceRetriever
from app.core.query_preprocessor import QueryPreprocessor
from app.core.intent_analyzer import IntentAnalyzer
from app.core.response_builder import ResponseBuilder

# 初始化组件
retriever = ResourceRetriever()
preprocessor = QueryPreprocessor()
analyzer = IntentAnalyzer()
response_builder = ResponseBuilder()

# 测试搜索"给我指数函数的资料"
query = "给我指数函数的资料"

print(f"====================================")
print(f"测试查询: {query}")
print(f"====================================")
print()

# 1. 意图理解
print("步骤1: 意图理解")
intent_result = analyzer.analyze(query)
print(f"  主要意图: {intent_result.get('intent', '')}")
print(f"  用户需求: {intent_result.get('user_needs', '')}")
print(f"  资源类型: {intent_result.get('resource_types', [])}")
print()

# 2. 资源检索
print("步骤2: 资源检索")
retrieved_resources = retriever.retrieve(
    query,
    intent_result.get('intent', 'search'),
    resource_types=intent_result.get('resource_types', [])
)
print(f"  教案: {len(retrieved_resources.get('lesson_plan_patterns', []))}条")
print(f"  习题: {len(retrieved_resources.get('exercise_resources', []))}条")
print(f"  课件: {len(retrieved_resources.get('courseware_resources', []))}条")
print(f"  教学大纲: {len(retrieved_resources.get('syllabus_resources', []))}条")
print()

# 3. 响应格式化
print("步骤3: 响应格式化")
state = {
    "user_needs": intent_result.get('user_needs', ''),
    "resource_types": intent_result.get('resource_types', []),
    "retrieved_resources": retrieved_resources
}
response = response_builder._format_resources(state)

print("响应内容:")
print(response)
