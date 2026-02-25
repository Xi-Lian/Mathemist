"""
简单测试指数函数资源检索
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_exponential_simple():
    """简单测试指数函数资源检索"""
    print("=" * 80)
    print("指数函数资源检索 - 简化版测试")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    print("=" * 80)
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索资源...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        print(f"\n📄 前50条教案:")
        
        for j, lp in enumerate(lesson_plans[:50], 1):
            relevance = lp.get('relevance', 0)
            title = lp.get('title', '未知')
            is_theme_match = lp.get('is_theme_match', False)
            is_conflict = lp.get('is_conflict_theme', False)
            source = lp.get('source', '')
            filename = Path(source).name if source else '未知'
            
            print(f"\n   {j:2d}. {title}")
            print(f"       文件: {filename}")
            print(f"       相似度: {relevance:.1%} | 主题匹配: {'✓' if is_theme_match else '✗'} | 冲突: {'✓' if is_conflict else '✗'}")
            
            if is_theme_match:
                match_evidence = lp.get('match_evidence', [])
                if match_evidence:
                    ev_type, ev_text = match_evidence[0]
                    print(f"       匹配依据: {ev_type}")
            
            if is_conflict:
                conflict_evidence = lp.get('conflict_evidence', [])
                if conflict_evidence:
                    conf_theme, _ = conflict_evidence[0]
                    print(f"       冲突主题: {conf_theme}")
        
        print(f"\n{'=' * 80}")
        print(f"查找4.2指数函数教案:")
        
        found_42 = False
        for j, lp in enumerate(lesson_plans):
            source = lp.get('source', '')
            if '4.2' in source or '指数函数' in source:
                relevance = lp.get('relevance', 0)
                title = lp.get('title', '未知')
                is_theme_match = lp.get('is_theme_match', False)
                filename = Path(source).name if source else '未知'
                print(f"\n   ✅ 找到! 排名第{j+1}位")
                print(f"      标题: {title}")
                print(f"      文件: {filename}")
                print(f"      相似度: {relevance:.1%} | 主题匹配: {'✓' if is_theme_match else '✗'}")
                found_42 = True
        
        if not found_42:
            print(f"\n   ❌ 未找到4.2指数函数教案!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_exponential_simple()
