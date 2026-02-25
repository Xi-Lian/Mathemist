"""
详细调试测试脚本
"""
import sys
from pathlib import Path

# 添加backend目录到路径
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever
from app.core.intent_analyzer import IntentAnalyzer


def debug_retrieval():
    """详细调试资源检索"""
    print("=" * 80)
    print("资源检索详细调试")
    print("=" * 80)
    
    test_query = "指数函数教学设计"
    
    print(f"\n🎯 测试查询: {test_query}")
    
    # 意图分析
    intent_analyzer = IntentAnalyzer()
    intent_result = intent_analyzer.analyze(test_query)
    print(f"\n📋 意图分析结果:")
    print(f"   主要意图: {intent_result.get('intent')}")
    print(f"   资源类型: {intent_result.get('resource_types')}")
    
    # 资源检索
    retriever = ResourceRetriever()
    resource_types = intent_result.get('resource_types', [])
    
    print(f"\n🔍 开始检索...")
    retrieved = retriever.retrieve(
        test_query,
        intent_result.get('intent'),
        resource_types=resource_types
    )
    
    # 检查结果
    print("\n" + "=" * 80)
    print("📊 结果分析")
    print("=" * 80)
    
    lesson_plans = retrieved.get('lesson_plan_patterns', [])
    print(f"\n📚 教案资源数量: {len(lesson_plans)}")
    
    if lesson_plans:
        print(f"\n📋 教案资源详情（前20条）:")
        print("-" * 80)
        for i, plan in enumerate(lesson_plans[:20]):
            title = plan.get('title', '未知')
            relevance = plan.get('relevance', 0)
            source = plan.get('source', '')
            filename = Path(source).name if source else '未知'
            
            is_theme_match = plan.get('is_theme_match', False)
            is_conflict = plan.get('is_conflict_theme', False)
            match_evidence = plan.get('match_evidence', [])
            conflict_evidence = plan.get('conflict_evidence', [])
            
            print(f"\n{i+1:2d}. 📄 {filename}")
            print(f"      相似度: {relevance:.2%}")
            print(f"      主题匹配: {'✅' if is_theme_match else '❌'}")
            print(f"      冲突主题: {'⚠️' if is_conflict else '✅'}")
            
            if match_evidence:
                evidence_type, evidence_text = match_evidence[0]
                print(f"      匹配依据: {evidence_type}")
            
            if conflict_evidence:
                conflict_theme, conflict_text = conflict_evidence[0]
                print(f"      冲突依据: {conflict_theme}")
            
            # 检查是否是4.2的
            if '4.2' in filename or '指数函数' in filename:
                print(f"      ⭐ 这是4.2指数函数的教案！")
        
        # 统计主题匹配情况
        theme_match_count = sum(1 for p in lesson_plans if p.get('is_theme_match'))
        conflict_count = sum(1 for p in lesson_plans if p.get('is_conflict_theme'))
        
        # 检查是否有4.2的教案
        has_42 = any('4.2' in Path(p.get('source', '')).name for p in lesson_plans)
        has_exponential = any('指数函数' in Path(p.get('source', '')).name for p in lesson_plans)
        
        print(f"\n" + "=" * 80)
        print(f"📊 教案资源统计:")
        print(f"   总数: {len(lesson_plans)}")
        print(f"   主题匹配: {theme_match_count} ({theme_match_count/len(lesson_plans)*100:.1f}%)")
        print(f"   冲突主题: {conflict_count} ({conflict_count/len(lesson_plans)*100:.1f}%)")
        print(f"   包含4.2: {'✅' if has_42 else '❌'}")
        print(f"   包含指数函数: {'✅' if has_exponential else '❌'}")
    
    print(f"\n   其他资源类型数量:")
    print(f"      理论资源: {len(retrieved.get('theory_resources', []))}")
    print(f"      习题资源: {len(retrieved.get('exercise_resources', []))}")
    print(f"      课件资源: {len(retrieved.get('courseware_resources', []))}")
    print(f"      课例资源: {len(retrieved.get('lesson_case_resources', []))}")
    print(f"      GGB资源: {len(retrieved.get('ggb_resources', []))}")
    print(f"      教学大纲: {len(retrieved.get('syllabus_resources', []))}")
    
    print("\n" + "=" * 80)
    print("调试完成！")
    print("=" * 80)


if __name__ == "__main__":
    debug_retrieval()
