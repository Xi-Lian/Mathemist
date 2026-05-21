"""
快速测试脚本 - 验证动态意图识别系统
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 快速测试用例 - 之前失败的查询
QUICK_TEST_CASES = [
    "三角函数应用题",
    "函数的奇偶性证明题",
    "二次函数的实际应用题",
    "高三二次函数难题"
]

def test_query(query):
    """测试单个查询"""
    url = f"{BASE_URL}/api/query"
    payload = {
        "query": query,
        "intent": "search",
        "resource_types": ["exercise"]
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"测试查询: {query}")
        print(f"{'='*60}")
        
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code == 200:
            response_json = response.json()
            if 'data' in response_json:
                data = response_json['data']
                if 'retrieved_resources' in data:
                    resources = data['retrieved_resources']
                    exercise_resources = resources.get('exercise_resources', [])
                    
                    if exercise_resources:
                        print(f"✅ 找到 {len(exercise_resources)} 道习题")
                        # 打印第一道习题的信息
                        first_resource = exercise_resources[0]
                        print(f"   第一道题: {first_resource.get('title', '无标题')}")
                        print(f"   相关性: {first_resource.get('relevance', '无')}")
                        print(f"   来源: {first_resource.get('source', '无')}")
                        return True
                    else:
                        print("❌ 未找到相关习题资源")
                        return False
        print(f"❌ 请求失败: {response.status_code}")
        return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def main():
    """主函数"""
    print("="*60)
    print("快速测试 - 验证动态意图识别系统")
    print("="*60)
    
    results = []
    for query in QUICK_TEST_CASES:
        success = test_query(query)
        results.append((query, success))
    
    # 打印汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    success_count = sum(1 for _, success in results if success)
    for i, (query, success) in enumerate(results, 1):
        status = "✅" if success else "❌"
        print(f"{i}. {status} {query}")
    
    print(f"\n测试完成: {success_count}/{len(QUICK_TEST_CASES)} 个查询成功")
    
    if success_count == len(QUICK_TEST_CASES):
        print("🎉 所有测试用例都通过了！动态意图识别系统工作正常！")
    else:
        print("⚠️  部分测试用例失败，需要进一步改进系统")


if __name__ == "__main__":
    main()