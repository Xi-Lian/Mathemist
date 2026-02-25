"""
测试主题匹配系统是否正确工作
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.theme_matcher import get_theme_matcher


def test_theme_matcher():
    """测试主题匹配器"""
    print("=" * 80)
    print("主题匹配系统测试")
    print("=" * 80)
    
    theme_matcher = get_theme_matcher()
    
    # 测试案例：模拟不同的教案资源
    test_cases = [
        {
            "name": "4.2指数函数的教案",
            "metadata": {
                "title": "4.2.1 指数函数的概念",
                "source_file": "教案/第四章指数函数与对数函数/4.2指数函数/4.2.1 指数函数的概念 教学设计（1）.md",
                "章节": "4.2",
                "知识点标签": "指数函数"
            },
            "document": "指数函数的概念：形如 y = a^x 的函数..."
        },
        {
            "name": "4.3对数函数的教案",
            "metadata": {
                "title": "4.3 对数的概念",
                "source_file": "教案/第四章指数函数与对数函数/4.3对数/4.3 对数的概念 教学设计.md",
                "章节": "4.3",
                "知识点标签": "对数"
            },
            "document": "对数的概念：如果 a^b = N，那么 b = log_a N..."
        },
        {
            "name": "5.1三角函数的教案",
            "metadata": {
                "title": "5.1 任意角和弧度制",
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
        print(f"\n📋 测试案例 {i+1}: {test_case['name']}")
        print(f"   文件名: {Path(test_case['metadata']['source_file']).name}")
        print(f"   路径: {test_case['metadata']['source_file']}")
        print(f"   章节: {test_case['metadata']['章节']}")
        print(f"   知识点标签: {test_case['metadata']['知识点标签']}")
        
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
    test_theme_matcher()
