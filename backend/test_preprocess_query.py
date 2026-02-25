from app.core.query_preprocessor import QueryPreprocessor
import json

# 初始化组件
preprocessor = QueryPreprocessor()

# 测试预处理"给我指数函数的资料"
query = "给我指数函数的资料"

print(f"原始查询: {query}")
print()

# 预处理查询
result = preprocessor.preprocess(query)

print(f"预处理结果:")
print(f"  原始查询: {result.get('original_query', '')}")
print(f"  清理后的查询: {result.get('cleaned_query', '')}")
print(f"  关键词: {result.get('keywords', [])}")
print(f"  核心概念: {result.get('core_concepts', [])}")
print(f"  LaTeX表达式: {result.get('latex_expressions', [])}")
print(f"  搜索版本: {result.get('search_versions', [])}")
print(f"  查询类型: {result.get('query_type', '')}")
print(f"  清晰度: {result.get('clarity', 0.0)}")
print()
print(f"  意图:")
intent = result.get('intent', {})
print(f"    主题: {intent.get('topic', '')}")
print(f"    资源类型: {intent.get('resource_types', [])}")
print(f"    操作: {intent.get('operation', '')}")
print(f"    质量: {intent.get('quality', '')}")
