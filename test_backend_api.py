#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json

print("=" * 70)
print("测试后端API")
print("=" * 70)

# 测试后端是否在运行
try:
    response = requests.get("http://localhost:8000/health", timeout=5)
    print(f"\n✅ 后端服务器正在运行")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text[:200]}")
except Exception as e:
    print(f"\n❌ 无法连接到后端服务器: {e}")
    print("请确保后端服务器正在运行（端口8000）")
    exit(1)

print("\n" + "=" * 70)
print("测试完成")
