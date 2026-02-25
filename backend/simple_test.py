import requests
import json

BASE_URL = "http://localhost:8000"

print("测试接口是否运行...")
try:
    response = requests.get(f"{BASE_URL}/health", timeout=5)
    print(f"✅ 服务运行正常！状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    print("\n测试资源反馈接口...")
    data = {
        "resource_id": "test-resource-001",
        "is_like": True,
        "query": "三角函数",
        "resource_type": "theory",
        "metadata": {"chapter": "第一章"},
        "dislike_reason": ""
    }
    response = requests.post(f"{BASE_URL}/feedback/resource", json=data, timeout=5)
    print(f"资源反馈状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
    print("\n测试建议反馈接口...")
    data = {
        "query": "二次函数",
        "suggestion": "希望增加更多的练习题",
        "contact": "user@example.com"
    }
    response = requests.post(f"{BASE_URL}/feedback/suggestion", json=data, timeout=5)
    print(f"建议反馈状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到服务，服务可能没有运行")
except Exception as e:
    print(f"❌ 错误: {e}")
