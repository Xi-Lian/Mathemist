"""
直接测试4.2指数函数教案的主题匹配
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.theme_matcher import get_theme_matcher


def test_42_lesson_plans():
    """测试4.2指数函数教案的主题匹配"""
    print("=" * 80)
    print("4.2指数函数教案主题匹配测试")
    print("=" * 80)
    
    theme_matcher = get_theme_matcher()
    
    # 4.2指数函数文件夹下的文件路径
    base_path = Path(__file__).parent.parent / "learning_resource" / "教案" / "第四章 指数函数与对数函数" / "4.2指数函数"
    
    test_files = [
        "４2.1 指数函数的概念 教学设计（1）.md",
        "《4.2 指数函数》名师精品教案教学设计.md",
        "4.2.2 指数函数的图像和性质 教学设计（1）.md",
    ]
    
    # 4.4对数函数文件夹下的文件（作为对比）
    base_path_44 = Path(__file__).parent.parent / "learning_resource" / "教案" / "第四章 指数函数与对数函数" / "4.4对数函数"
    
    test_files_44 = [
        "4.4.1 对数函数的概念 教学设计（1）.md",
        "《4.4 对数函数》名师精品教案教学设计.md",
    ]
    
    core_theme = "指数函数"
    print(f"\n🎯 测试主题: {core_theme}")
    print("-" * 80)
    
    # 测试4.2的文件
    print("\n📋 测试4.2指数函数的教案:")
    print("-" * 80)
    for filename in test_files:
        file_path = base_path / filename
        source_file = str(file_path)
        
        # 构造元数据
        metadata = {
            "title": filename.replace(".md", ""),
            "source_file": source_file,
            "章节": "4.2",
            "知识点标签": "指数函数"
        }
        
        # 读取文件内容（前500字符）
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
        except Exception as e:
            content = f"无法读取文件: {e}"
        
        result = theme_matcher.match_theme(
            core_theme=core_theme,
            metadata=metadata,
            document=content,
            verbose=True
        )
        
        print(f"\n📄 {filename}")
        print(f"   主题匹配: {'✅' if result['is_theme_match'] else '❌'}")
        print(f"   冲突主题: {'⚠️' if result['is_conflict_theme'] else '✅'}")
        print(f"   加分: +{result['relevance_boost']:.0%}")
        print(f"   减分: -{result['relevance_penalty']:.0%}")
        if result['match_evidence']:
            evidence_type, evidence_text = result['match_evidence'][0]
            print(f"   匹配依据: {evidence_type}")
        if result['conflict_evidence']:
            conflict_theme, conflict_text = result['conflict_evidence'][0]
            print(f"   冲突依据: {conflict_theme}")
    
    # 测试4.4的文件（对比）
    print("\n" + "=" * 80)
    print("📋 测试4.4对数函数的教案（作为对比）:")
    print("=" * 80)
    for filename in test_files_44:
        file_path = base_path_44 / filename
        source_file = str(file_path)
        
        # 构造元数据
        metadata = {
            "title": filename.replace(".md", ""),
            "source_file": source_file,
            "章节": "4.4",
            "知识点标签": "对数函数"
        }
        
        # 读取文件内容（前500字符）
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(500)
        except Exception as e:
            content = f"无法读取文件: {e}"
        
        result = theme_matcher.match_theme(
            core_theme=core_theme,
            metadata=metadata,
            document=content,
            verbose=False
        )
        
        print(f"\n📄 {filename}")
        print(f"   主题匹配: {'✅' if result['is_theme_match'] else '❌'}")
        print(f"   冲突主题: {'⚠️' if result['is_conflict_theme'] else '✅'}")
        print(f"   加分: +{result['relevance_boost']:.0%}")
        print(f"   减分: -{result['relevance_penalty']:.0%}")
        if result['match_evidence']:
            evidence_type, evidence_text = result['match_evidence'][0]
            print(f"   匹配依据: {evidence_type}")
        if result['conflict_evidence']:
            conflict_theme, conflict_text = result['conflict_evidence'][0]
            print(f"   冲突依据: {conflict_theme}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_42_lesson_plans()
