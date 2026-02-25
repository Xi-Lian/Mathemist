"""
简单测试：只查找4.2指数函数教案
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_short():
    """简单测试"""
    print("=" * 80)
    print("简单测试")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        
        print(f"\n📄 前5个教案:")
        for j, lp in enumerate(lesson_plans[:5]):
            source = lp.get('source', '')
            relevance = lp.get('relevance', 0)
            theme_match = lp.get('theme_match', False)
            conflict = lp.get('conflict_theme', False)
            filename = Path(source).name if source else '未知'
            print(f"\n{'=' * 80}")
            print(f"{j+1}. {filename}")
            print(f"   相似度: {relevance:.1%}")
            print(f"   主题匹配: {'是' if theme_match else '否'}")
            print(f"   冲突主题: {'是' if conflict else '否'}")
            if 'theme_boost' in lp:
                print(f"   主题加分: +{lp['theme_boost']:.1%}")
            if 'conflict_penalty' in lp:
                print(f"   冲突减分: -{lp['conflict_penalty']:.1%}")
            if 'base_relevance' in lp:
                print(f"   基础分: {lp['base_relevance']:.1%}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_short()
