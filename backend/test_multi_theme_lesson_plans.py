"""
测试多个数学主题的教案生成功能
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever
from app.core.lesson_plan_generator import LessonPlanGenerator


def test_multi_theme_lesson_plans():
    """测试多个数学主题的教案生成"""
    print("=" * 80)
    print("多主题教案生成测试")
    print("=" * 80)
    
    test_themes = [
        {
            "name": "指数函数",
            "query": "指数函数的概念 教学设计"
        },
        {
            "name": "对数函数",
            "query": "对数函数的图像和性质 教案"
        },
        {
            "name": "三角函数",
            "query": "正弦函数的图像 教学设计"
        },
        {
            "name": "二次函数",
            "query": "二次函数的顶点式 教案"
        }
    ]
    
    retriever = ResourceRetriever()
    generator = LessonPlanGenerator()
    
    for i, theme_test in enumerate(test_themes):
        theme_name = theme_test["name"]
        query = theme_test["query"]
        
        print(f"\n{'=' * 80}")
        print(f"📋 测试 {i+1}/{len(test_themes)}: {theme_name}")
        print(f"📝 查询: {query}")
        print("=" * 80)
        
        try:
            print(f"\n🔍 开始检索资源...")
            results = retriever.retrieve(query, intent="lesson_plan")
            
            print(f"\n📊 检索结果摘要:")
            lesson_plans = results.get("lesson_plan_patterns", [])
            theory_resources = results.get("theory_resources", [])
            print(f"   教案示例: {len(lesson_plans)}条")
            print(f"   理论资源: {len(theory_resources)}条")
            
            if lesson_plans:
                print(f"\n📄 前3个教案示例:")
                for j, lp in enumerate(lesson_plans[:3], 1):
                    relevance = lp.get('relevance', 0)
                    title = lp.get('title', '未知')
                    print(f"   {j}. {title} (相似度: {relevance:.1%})")
            
            print(f"\n📝 开始生成教案...")
            lesson_plan = generator.generate(
                user_input=query,
                theory_resources=theory_resources,
                lesson_plan_patterns=lesson_plans
            )
            
            print(f"\n✅ 教案生成成功！")
            print(f"📄 教案长度: {len(lesson_plan)}字符")
            
            print(f"\n📋 教案预览 (前500字符):")
            print("-" * 80)
            print(lesson_plan[:500] + "..." if len(lesson_plan) > 500 else lesson_plan)
            print("-" * 80)
            
        except Exception as e:
            print(f"\n❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("所有主题测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_multi_theme_lesson_plans()
