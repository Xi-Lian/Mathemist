#!/usr/bin/env python3
import sys
sys.path.insert(0, 'd:\\Git_Repository\\Mathemist\\backend')

from app.core.intent.service import IntentAnalyzer

# 测试查询
query = "找一下关于分类加法计数原理的练习课课件"

# 创建分析器
analyzer = IntentAnalyzer()

# 分析意图
result = analyzer.analyze(query)

print("=" * 80)
print(f"查询: {query}")
print("=" * 80)
print(f"主要意图: {result.get('intent')}")
print(f"资源类型: {result.get('resource_types')}")
print(f"用户需求: {result.get('user_needs')}")
print("=" * 80)
print(f"完整结果: {result}")
