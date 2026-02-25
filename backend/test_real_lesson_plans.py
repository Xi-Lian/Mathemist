"""
测试真实教案资源的主题匹配
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.theme_matcher import get_theme_matcher
from app.core.resource_table_parser import ResourceTableParser


def test_real_lesson_plans():
    """测试真实教案资源的主题匹配"""
    print("=" * 80)
    print("真实教案资源主题匹配测试")
    print("=" * 80)
    
    theme_matcher = get_theme_matcher()
    
    # 获取资源表解析器
    learning_resource_path = Path(__file__).parent.parent / "learning_resource"
    parser = ResourceTableParser(str(learning_resource_path))
    
    # 获取所有教案资源
    print("\n📂 加载资源表...")
    resources = parser.parse_resource_table()
    
    lesson_plans = [r for r in resources if r.get('type') == 'lesson_plan']
    print(f"✅ 共找到 {len(lesson_plans)} 个教案资源")
    
    core_theme = "指数函数"
    print(f"\n🎯 测试主题: {core_theme}")
    print("-" * 80)
    
    # 测试所有教案资源
    results = []
    for i, plan in enumerate(lesson_plans[:50]):  # 只测试前50个，避免太多输出
        metadata = plan.get('metadata', {})
        doc = plan.get('content', '')
        
        result = theme_matcher.match_theme(
            core_theme=core_theme,
            metadata=metadata,
            document=doc,
            verbose=False
        )
        
        results.append({
            "index": i,
            "title": metadata.get('title', '未知'),
            "source_file": metadata.get('source_file', ''),
            "is_theme_match": result["is_theme_match"],
            "is_conflict_theme": result["is_conflict_theme"],
            "relevance_boost": result["relevance_boost"],
            "relevance_penalty": result["relevance_penalty"],
            "match_evidence": result["match_evidence"],
            "conflict_evidence": result["conflict_evidence"]
        })
    
    # 分类显示结果
    print("\n📋 结果分类:")
    print("-" * 80)
    
    # 1. 主题匹配成功的
    matched = [r for r in results if r["is_theme_match"]]
    print(f"\n✅ 主题匹配成功 ({len(matched)}个):")
    for r in matched[:10]:  # 只显示前10个
        filename = Path(r["source_file"]).name
        print(f"   {r['index']+1}. {filename}")
        if r['match_evidence']:
            evidence_type, evidence_text = r['match_evidence'][0]
            print(f"      匹配依据: {evidence_type}")
        print(f"      加分: +{r['relevance_boost']:.0%}")
    
    # 2. 冲突主题的
    conflict = [r for r in results if r["is_conflict_theme"]]
    print(f"\n⚠️ 冲突主题 ({len(conflict)}个):")
    for r in conflict[:10]:  # 只显示前10个
        filename = Path(r["source_file"]).name
        print(f"   {r['index']+1}. {filename}")
        if r['conflict_evidence']:
            conflict_theme, conflict_text = r['conflict_evidence'][0]
            print(f"      冲突主题: {conflict_theme}")
        print(f"      减分: -{r['relevance_penalty']:.0%}")
    
    # 3. 不匹配的
    unmatched = [r for r in results if not r["is_theme_match"] and not r["is_conflict_theme"]]
    print(f"\n❌ 不匹配 ({len(unmatched)}个)")
    
    # 特别检查4.2的教案
    print(f"\n" + "=" * 80)
    print("🔍 特别检查4.2指数函数的教案:")
    print("=" * 80)
    
    for r in results:
        source_file = r["source_file"]
        if "4.2" in source_file or "指数函数" in Path(source_file).name:
            filename = Path(source_file).name
            print(f"\n📄 {filename}")
            print(f"   主题匹配: {'✅' if r['is_theme_match'] else '❌'}")
            print(f"   冲突主题: {'⚠️' if r['is_conflict_theme'] else '✅'}")
            print(f"   加分: +{r['relevance_boost']:.0%}")
            print(f"   减分: -{r['relevance_penalty']:.0%}")
            if r['match_evidence']:
                evidence_type, evidence_text = r['match_evidence'][0]
                print(f"   匹配依据: {evidence_type}")
            if r['conflict_evidence']:
                conflict_theme, conflict_text = r['conflict_evidence'][0]
                print(f"   冲突依据: {conflict_theme}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_real_lesson_plans()
