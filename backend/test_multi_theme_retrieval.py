"""
测试多个数学主题的资源检索功能
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_multi_theme_retrieval():
    """测试多个数学主题的资源检索"""
    print("=" * 80)
    print("多主题资源检索测试")
    print("=" * 80)
    
    test_themes = [
        {
            "name": "指数函数",
            "query": "指数函数的概念"
        },
        {
            "name": "对数函数",
            "query": "对数函数的图像和性质"
        },
        {
            "name": "三角函数",
            "query": "正弦函数的图像"
        },
        {
            "name": "二次函数",
            "query": "二次函数的顶点式"
        }
    ]
    
    retriever = ResourceRetriever()
    
    for i, theme_test in enumerate(test_themes):
        theme_name = theme_test["name"]
        query = theme_test["query"]
        
        print(f"\n{'=' * 80}")
        print(f"📋 测试 {i+1}/{len(test_themes)}: {theme_name}")
        print(f"📝 查询: {query}")
        print("=" * 80)
        
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
                print(f"\n📄 前3个教案示例:")
                for j, lp in enumerate(lesson_plans[:3], 1):
                    relevance = lp.get('relevance', 0)
                    title = lp.get('title', '未知')
                    is_theme_match = lp.get('is_theme_match', False)
                    print(f"   {j}. {title}")
                    print(f"      相似度: {relevance:.1%}, 主题匹配: {'是' if is_theme_match else '否'}")
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("所有主题测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_multi_theme_retrieval()
