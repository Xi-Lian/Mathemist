"""
简单的 API 测试脚本，用于找出哪个端点有问题
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_response(response):
    print(f"状态码: {response.status_code}")
    try:
        data = response.json()
        print(f"响应内容:\n{json.dumps(data, ensure_ascii=False, indent=2)}")
        return data
    except:
        print(f"响应内容: {response.text}")
        return None

print_section("开始测试各个 API 端点")

# 1. 首先创建一个用户
print("\n--- 1. 创建用户 ---")
user_data = {
    "username": "debug_user",
    "email": "debug@example.com"
}
response = requests.post(f"{BASE_URL}/users", json=user_data)
user = print_response(response)
if not user or response.status_code != 200:
    print("❌ 用户创建失败")
    exit(1)
user_id = user["user_id"]
print(f"✅ 用户创建成功，用户ID: {user_id}")

# 2. 测试为用户创建线程
print("\n--- 2. 为用户创建线程 ---")
thread_data = {
    "metadata": {"test": "debug"}
}
response = requests.post(f"{BASE_URL}/users/{user_id}/threads", json=thread_data)
thread = print_response(response)
if not thread or response.status_code != 200:
    print("❌ 创建用户线程失败")
    exit(1)
thread_id = thread["thread_id"]
print(f"✅ 创建用户线程成功，线程ID: {thread_id}")

# 3. 测试获取用户线程列表
print("\n--- 3. 获取用户线程列表 ---")
response = requests.get(f"{BASE_URL}/users/{user_id}/threads")
print_response(response)

# 4. 测试创建运行
print("\n--- 4. 创建运行 ---")
run_data = {
    "assistant_id": "math_assistant",
    "input": {
        "messages": [
            {"type": "human", "content": "你好"}
        ]
    }
}
response = requests.post(f"{BASE_URL}/threads/{thread_id}/runs", json=run_data)
print_response(response)

# 5. 测试获取用户运行列表
print("\n--- 5. 获取用户运行列表 ---")
response = requests.get(f"{BASE_URL}/users/{user_id}/runs")
print_response(response)

print_section("测试完成")