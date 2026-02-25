"""
只查看前10条结果的详细情况
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_exponential_top10():
    """查看前10条结果的详细情况"""
    print("=" * 80)
    print("前10条结果详细分析")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        print(f"\n📄 前10条详细信息:")
        print("=" * 80)
        
        for j, lp in enumerate(lesson_plans[:10], 1):
            relevance = lp.get('relevance', 0)
            title = lp.get('title', '未知')
            is_theme_match = lp.get('is_theme_match', False)
            is_conflict = lp.get('is_conflict_theme', False)
            source = lp.get('source', '')
            filename = Path(source).name if source else '未知'
            
            print(f"\n{'=' * 80}")
            print(f"【第 {j} 名】")
            print(f"标题: {title}")
            print(f"文件: {filename}")
            print(f"路径: {source}")
            print(f"相似度: {relevance:.1%}")
            print(f"主题匹配: {'✓ 是' if is_theme_match else '✗ 否'}")
            print(f"冲突主题: {'✓ 是' if is_conflict else '✗ 否'}")
            
            match_evidence = lp.get('match_evidence', [])
            if match_evidence:
                print(f"\n匹配依据:")
                for ev_type, ev_text in match_evidence:
                    print(f"  - {ev_type}: {ev_text}")
            
            conflict_evidence = lp.get('conflict_evidence', [])
            if conflict_evidence:
                print(f"\n冲突依据:")
                for conf_theme, conf_text in conflict_evidence:
                    print(f"  - {conf_theme}: {conf_text[:80]}...")
        
        print(f"\n{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_exponential_top10()
