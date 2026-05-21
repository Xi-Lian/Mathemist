import sys
import os
sys.path.insert(0, 'app')

# 设置环境变量
os.environ["APP_VERBOSE_LOGS"] = "1"

# 测试 normalize_resource_type 函数
from core.retrieval.classify_results_helpers.resource_type import normalize_resource_type

# 测试用例
test_cases = [
    # 原始测试：source_file包含课件关键词
    {
        "metadata": {
            "source_file": "03-概率与统计/课件/组合数课件.pptx",
            "title": "组合数",
            "教学用途": "练习课课件"
        },
        "resource_type": "theory",
        "expected": "courseware"
    },
    # 新测试：title包含课件关键词
    {
        "metadata": {
            "source_file": "03-概率与统计/课件/组合数.pptx",
            "title": "组合数课件",
            "教学用途": "练习课课件"
        },
        "resource_type": "theory",
        "expected": "courseware"
    },
    # 新测试：教学用途包含课件关键词（这是用户的情况）
    {
        "metadata": {
            "source_file": "03-概率与统计/课件/6.2.3组合.pptx",
            "title": "6.2.3组合＋6.2.4组合数",
            "教学用途": "练习课课件"
        },
        "resource_type": "theory",
        "expected": "courseware"
    },
    # 测试：教学用途包含复习课课件
    {
        "metadata": {
            "source_file": "03-概率与统计/课件/复习.pptx",
            "title": "概率统计复习",
            "教学用途": "复习课课件"
        },
        "resource_type": "theory",
        "expected": "courseware"
    },
    # 测试：教学用途包含习题课课件
    {
        "metadata": {
            "source_file": "03-概率与统计/课件/习题.pptx",
            "title": "概率统计习题",
            "教学用途": "习题课课件"
        },
        "resource_type": "theory",
        "expected": "courseware"
    }
]

print("测试 normalize_resource_type 函数修复效果：")
print("=" * 80)

passed = 0
failed = 0

for i, test_case in enumerate(test_cases):
    metadata = test_case["metadata"]
    resource_type = test_case["resource_type"]
    expected = test_case["expected"]
    
    result = normalize_resource_type(metadata, resource_type)
    
    status = "✅ PASS" if result == expected else "❌ FAIL"
    print(f"\n测试用例 {i+1}: {status}")
    print(f"  输入:")
    print(f"    source_file: {metadata['source_file']}")
    print(f"    title: {metadata['title']}")
    print(f"    教学用途: {metadata['教学用途']}")
    print(f"    resource_type: {resource_type}")
    print(f"  期望输出: {expected}")
    print(f"  实际输出: {result}")
    
    if result == expected:
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 80)
print(f"测试结果: {passed} 个通过, {failed} 个失败")
