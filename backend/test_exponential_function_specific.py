"""
专门测试指数函数的概念教学设计资源检索
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_exponential_function_retrieval():
    """测试指数函数的概念教学设计资源检索"""
    print("=" * 80)
    print("指数函数概念教学设计资源检索测试")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    print("=" * 80)
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索资源...")
        results = retriever.retrieve(query, intent="search")
        
        print(f"\n📊 检索结果摘要:")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        theory_resources = results.get("theory_resources", [])
        exercises = results.get("exercise_resources", [])
        coursewares = results.get("courseware_resources", [])
        
        print(f"   教案示例: {len(lesson_plans)}条")
        print(f"   理论资源: {len(theory_resources)}条")
        print(f"   习题资源: {len(exercises)}条")
        print(f"   课件资源: {len(coursewares)}条")
        
        if lesson_plans:
            print(f"\n📄 所有教案示例详情:")
            for j, lp in enumerate(lesson_plans, 1):
                relevance = lp.get('relevance', 0)
                title = lp.get('title', '未知')
                is_theme_match = lp.get('is_theme_match', False)
                is_conflict = lp.get('is_conflict_theme', False)
                source = lp.get('source', '')
                filename = Path(source).name if source else '未知'
                
                print(f"\n   {j}. {title}")
                print(f"      文件: {filename}")
                print(f"      相似度: {relevance:.1%}")
                print(f"      主题匹配: {'是' if is_theme_match else '否'}")
                print(f"      冲突主题: {'是' if is_conflict else '否'}")
                
                match_evidence = lp.get('match_evidence', [])
                if match_evidence:
                    print(f"      匹配依据:")
                    for ev_type, ev_text in match_evidence:
                        print(f"        - {ev_type}: {ev_text}")
                
                conflict_evidence = lp.get('conflict_evidence', [])
                if conflict_evidence:
                    print(f"      冲突依据:")
                    for conf_theme, conf_text in conflict_evidence:
                        print(f"        - {conf_theme}: {conf_text[:60]}...")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_exponential_function_retrieval()
