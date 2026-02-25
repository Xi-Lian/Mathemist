"""
查找4.2指数函数文件在检索结果中的位置
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_find_42_files():
    """查找4.2指数函数文件"""
    print("=" * 80)
    print("查找4.2指数函数文件位置")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        
        print(f"\n🔍 查找4.2指数函数文件:")
        found = False
        
        for j, lp in enumerate(lesson_plans):
            source = lp.get('source', '')
            if '4.2' in source and '指数函数' in source:
                relevance = lp.get('relevance', 0)
                title = lp.get('title', '未知')
                is_theme_match = lp.get('is_theme_match', False)
                is_conflict = lp.get('is_conflict_theme', False)
                filename = Path(source).name if source else '未知'
                
                print(f"\n{'=' * 80}")
                print(f"✅ 找到4.2指数函数文件!")
                print(f"排名: 第 {j+1} 位")
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
                
                found = True
        
        if not found:
            print(f"\n❌ 未找到4.2指数函数文件!")
            
            print(f"\n📄 前20条结果:")
            for j, lp in enumerate(lesson_plans[:20], 1):
                source = lp.get('source', '')
                filename = Path(source).name if source else '未知'
                relevance = lp.get('relevance', 0)
                print(f"   {j:2d}. {filename} (相似度: {relevance:.1%})")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_find_42_files()
