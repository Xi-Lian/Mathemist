#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 build_resource_type_filters 函数
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.retrieval.retrieve_helpers.filters import build_resource_type_filters

# 测试我们的场景
query = "组合数 练习课 课件"
resource_types = ['课件', 'PPT', '教学设计', '习题', '练习题']
question_type = None

print("=" * 80)
print("测试 build_resource_type_filters")
print("=" * 80)
print(f"query: {query}")
print(f"resource_types: {resource_types}")
print()

resource_type_filters, where_filter = build_resource_type_filters(query, resource_types, question_type)

print()
print(f"resource_type_filters: {resource_type_filters}")
print(f"where_filter: {where_filter}")

print()
print("=" * 80)
