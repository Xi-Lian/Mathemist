"""
调试测试 - 查看第三章教案为什么被标记为冲突
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.theme_matcher import get_theme_matcher


def test_chapter3_lesson_plan():
    """测试第三章教案的主题匹配"""
    theme_matcher = get_theme_matcher()
    
    # 模拟一个第三章的教案
    metadata = {
        "title": "3.2.1单调性与最大（小）值 教学设计（1）",
        "source_file": "教案/第三章 函数的概念与性质/3.2函数的基本性质/3.2.1单调性与最大（小）值 教学设计（1）.md",
        "章节": "3.2",
        "知识点标签": "函数的基本性质, 单调性"
    }
    
    document = "函数的单调性的概念..."
    
    print("=" * 80)
    print("测试第三章教案的主题匹配")
    print("=" * 80)
    print(f"\n📄 文件名: {Path(metadata['source_file']).name}")
    print(f"📋 标题: {metadata['title']}")
    
    print(f"\n🎯 测试主题: 指数函数")
    result = theme_matcher.match_theme(
        core_theme="指数函数",
        metadata=metadata,
        document=document,
        verbose=True
    )
    
    print(f"\n" + "=" * 80)
    print("结果:")
    print(f"   is_theme_match: {result['is_theme_match']}")
    print(f"   is_conflict_theme: {result['is_conflict_theme']}")
    print(f"   relevance_boost: {result['relevance_boost']}")
    print(f"   relevance_penalty: {result['relevance_penalty']}")
    print(f"   match_evidence: {result['match_evidence']}")
    print(f"   conflict_evidence: {result['conflict_evidence']}")
    print("=" * 80)


if __name__ == "__main__":
    test_chapter3_lesson_plan()
