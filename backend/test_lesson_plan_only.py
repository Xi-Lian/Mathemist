"""
测试指数函数教学设计检索
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever
from app.core.intent_analyzer import IntentAnalyzer


def test_lesson_plan_retrieval():
    """测试教案检索"""
    print("=" * 80)
    print("测试：指数函数教学设计检索")
    print("=" * 80)
    
    test_query = "指数函数教学设计"
    
    print(f"\n📝 查询: {test_query}")
    
    # 意图分析
    print("\n1. 意图分析")
    intent_analyzer = IntentAnalyzer()
    intent_result = intent_analyzer.analyze(test_query)
    print(f"   主要意图: {intent_result.get('intent')}")
    print(f"   资源类型: {intent_result.get('resource_types')}")
    print(f"   用户需求: {intent_result.get('user_needs')}")
    
    # 资源检索
    print("\n2. 资源检索")
    retriever = ResourceRetriever()
    resource_types = intent_result.get('resource_types', [])
    print(f"   使用资源类型过滤: {resource_types}")
    
    retrieved = retriever.retrieve(
        test_query,
        intent_result.get('intent'),
        resource_types=resource_types
    )
    
    # 检查结果
    print("\n3. 检索结果分析")
    
    lesson_plans = retrieved.get('lesson_plan_patterns', [])
    print(f"\n   教案资源数量: {len(lesson_plans)}")
    
    if lesson_plans:
        print("\n   教案资源详情（前5条）:")
        for i, plan in enumerate(lesson_plans[:5]):
            print(f"\n   {i+1}. 标题: {plan.get('title')}")
            print(f"      相似度: {plan.get('relevance'):.2%}")
            print(f"      主题匹配: {'✅' if plan.get('is_theme_match') else '❌'}")
            print(f"      冲突主题: {'⚠️' if plan.get('is_conflict_theme') else '✅'}")
            print(f"      来源: {plan.get('source')}")
        
        theme_match_count = sum(1 for p in lesson_plans if p.get('is_theme_match'))
        conflict_count = sum(1 for p in lesson_plans if p.get('is_conflict_theme'))
        print(f"\n   📊 教案资源统计:")
        print(f"      总数: {len(lesson_plans)}")
        print(f"      主题匹配: {theme_match_count} ({theme_match_count/len(lesson_plans)*100:.1f}%)")
        print(f"      冲突主题: {conflict_count} ({conflict_count/len(lesson_plans)*100:.1f}%)")
    
    print(f"\n   其他资源类型数量:")
    print(f"      理论资源: {len(retrieved.get('theory_resources', []))}")
    print(f"      习题资源: {len(retrieved.get('exercise_resources', []))}")
    print(f"      课件资源: {len(retrieved.get('courseware_resources', []))}")
    print(f"      课例资源: {len(retrieved.get('lesson_case_resources', []))}")
    print(f"      GGB资源: {len(retrieved.get('ggb_resources', []))}")
    print(f"      教学大纲: {len(retrieved.get('syllabus_resources', []))}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    test_lesson_plan_retrieval()
