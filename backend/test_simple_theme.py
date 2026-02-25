"""
简单直接的主题匹配测试
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.theme_matcher import get_theme_matcher


def test_simple():
    """简单测试"""
    print("=" * 80)
    print("简单主题匹配测试")
    print("=" * 80)
    
    theme_matcher = get_theme_matcher()
    
    test_cases = [
        {
            "name": "4.2指数函数教案",
            "metadata": {
                "title": "4.2.1 指数函数的概念 教学设计（1）",
                "source_file": "教案/第四章 指数函数与对数函数/4.2指数函数/4.2.1 指数函数的概念 教学设计（1）.md",
                "章节": "4.2",
                "知识点标签": "指数函数"
            },
            "document": "指数函数的概念：形如 y = a^x 的函数，其中 a > 0 且 a ≠ 1..."
        },
        {
            "name": "4.4对数函数教案",
            "metadata": {
                "title": "4.4.1 对数函数的概念 教学设计（1）",
                "source_file": "教案/第四章 指数函数与对数函数/4.4对数函数/4.4.1 对数函数的概念 教学设计（1）.md",
                "章节": "4.4",
                "知识点标签": "对数函数"
            },
            "document": "对数函数的概念：形如 y = log_a x 的函数，其中 a > 0 且 a ≠ 1... 与指数函数互为反函数..."
        },
        {
            "name": "5.1三角函数教案",
            "metadata": {
                "title": "5.1 任意角和弧度制 教学设计",
                "source_file": "教案/第五章三角函数/5.1任意角和弧度制/5.1 任意角和弧度制 教学设计.md",
                "章节": "5.1",
                "知识点标签": "三角函数"
            },
            "document": "任意角的概念：角可以看成平面内一条射线绕着端点从一个位置旋转到另一个位置所成的图形..."
        }
    ]
    
    core_theme = "指数函数"
    print(f"\n🎯 测试主题: {core_theme}")
    print("-" * 80)
    
    for i, test_case in enumerate(test_cases):
        print(f"\n📋 测试 {i+1}: {test_case['name']}")
        
        result = theme_matcher.match_theme(
            core_theme=core_theme,
            metadata=test_case["metadata"],
            document=test_case["document"],
            verbose=True
        )
        
        print(f"\n   结果:")
        print(f"   ✅ 主题匹配: {'是' if result['is_theme_match'] else '否'}")
        print(f"   ⚠️ 冲突主题: {'是' if result['is_conflict_theme'] else '否'}")
        print(f"   ➕ 加分: {result['relevance_boost']:.2%}")
        print(f"   ➖ 减分: {result['relevance_penalty']:.2%}")
        
        if result['match_evidence']:
            print(f"   📝 匹配依据:")
            for evidence_type, evidence_text in result['match_evidence']:
                print(f"      - {evidence_type}: {evidence_text}")
        
        if result['conflict_evidence']:
            print(f"   🚫 冲突依据:")
            for conflict_theme, conflict_text in result['conflict_evidence']:
                print(f"      - {conflict_theme}: {conflict_text[:50]}...")
        
        print("-" * 80)
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_simple()
