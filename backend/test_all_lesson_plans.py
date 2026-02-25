"""
检查所有教案结果，找到4.2指数函数文件的位置
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_all_lesson_plans():
    """检查所有教案结果"""
    print("=" * 80)
    print("检查所有教案结果")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        
        print(f"\n🔍 在所有教案结果中查找4.2指数函数文件:")
        found = False
        first_42_position = None
        
        for j, lp in enumerate(lesson_plans):
            source = lp.get('source', '')
            if '4.2' in source and '指数函数' in source and '4.4' not in source:
                relevance = lp.get('relevance', 0)
                title = lp.get('title', '未知')
                filename = Path(source).name if source else '未知'
                
                if first_42_position is None:
                    first_42_position = j + 1
                
                print(f"\n{'=' * 80}")
                print(f"✅ 找到4.2指数函数文件!")
                print(f"排名: 第 {j+1} 位")
                print(f"标题: {title}")
                print(f"文件: {filename}")
                print(f"路径: {source}")
                print(f"相似度: {relevance:.1%}")
                
                found = True
        
        if found:
            print(f"\n{'=' * 80}")
            print(f"🎉 总结:")
            print(f"   第一个4.2指数函数文件在第 {first_42_position} 位")
            print(f"   总教案数: {len(lesson_plans)}")
            
            print(f"\n📄 前10个教案:")
            for j, lp in enumerate(lesson_plans[:10]):
                source = lp.get('source', '')
                relevance = lp.get('relevance', 0)
                filename = Path(source).name if source else '未知'
                print(f"   {j+1:2d}. {filename} (相似度: {relevance:.1%})")
        else:
            print(f"\n❌ 没有找到任何4.2指数函数文件!")
            print(f"\n📄 前20个教案:")
            for j, lp in enumerate(lesson_plans[:20]):
                source = lp.get('source', '')
                relevance = lp.get('relevance', 0)
                filename = Path(source).name if source else '未知'
                print(f"   {j+1:2d}. {filename} (相似度: {relevance:.1%})")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_all_lesson_plans()
