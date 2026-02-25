"""
测试反馈接口
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_resource_feedback():
    """测试资源反馈接口"""
    print("\n测试资源反馈接口...")
    try:
        data = {
            "resource_id": "test-resource-001",
            "is_like": True,
            "query": "三角函数",
            "resource_type": "theory",
            "metadata": {"chapter": "第一章"},
            "dislike_reason": ""
        }
        response = requests.post(f"{BASE_URL}/feedback/resource", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_suggestion_feedback():
    """测试建议反馈接口"""
    print("\n测试建议反馈接口...")
    try:
        data = {
            "query": "二次函数",
            "suggestion": "希望增加更多的练习题",
            "contact": "user@example.com"
        }
        response = requests.post(f"{BASE_URL}/feedback/suggestion", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_invalid_resource_feedback():
    """测试无效的资源反馈（缺少 resource_id）"""
    print("\n测试无效的资源反馈（缺少 resource_id）...")
    try:
        data = {
            "is_like": True,
            "query": "三角函数"
        }
        response = requests.post(f"{BASE_URL}/feedback/resource", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

def test_invalid_suggestion_feedback():
    """测试无效的建议反馈（缺少 suggestion）"""
    print("\n测试无效的建议反馈（缺少 suggestion）...")
    try:
        data = {
            "query": "二次函数",
            "contact": "user@example.com"
        }
        response = requests.post(f"{BASE_URL}/feedback/suggestion", json=data)
        print(f"状态码: {response.status_code}")
        print(f"响应: {json.dumps(response.json(), ensure_ascii=False, indent=2)}")
        return True
    except Exception as e:
        print(f"错误: {e}")
        return False

if __name__ == "__main__":
    print("="*70)
    print("反馈接口测试")
    print("="*70)
    
    if test_health():
        test_resource_feedback()
        test_suggestion_feedback()
        test_invalid_resource_feedback()
        test_invalid_suggestion_feedback()
    
    print("\n" + "="*70)
    print("测试完成")
    print("="*70)
