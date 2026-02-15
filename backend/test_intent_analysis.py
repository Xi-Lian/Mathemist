import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.intent_analyzer import IntentAnalyzer

# 初始化意图分析器
analyzer = IntentAnalyzer()

# 测试查询
test_queries = [
    "查找指数函数的课件和课例",
    "查找指数函数课例",
    "查找指数函数课件",
    "查找指数函数习题"
]

print("=" * 80)
print("测试意图识别")
print("=" * 80)

for query in test_queries:
    print(f"\n查询: {query}")
    result = analyzer.analyze(query)
    print(f"  - 意图: {result.get('intent')}")
    print(f"  - 用户需求: {result.get('user_needs')}")
    print(f"  - 资源类型: {result.get('resource_types')}")
    print(f"  - 所有意图: {result.get('intents')}")
