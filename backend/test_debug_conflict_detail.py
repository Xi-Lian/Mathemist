"""
详细调试测试脚本 - 查看冲突详情
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
    print("资源检索详细调试 - 查看冲突详情")
    print("=" * 80)
    
    test_query = "指数函数教学设计"
    
    print(f"\n🎯 测试查询: {test_query}")
    
    # 意图分析
    intent_analyzer = IntentAnalyzer()
    intent_result = intent_analyzer.analyze(test_query)
    
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
    lesson_plans = retrieved.get('lesson_plan_patterns', [])
    
    # 找一个有冲突的第三章教案
    print("\n" + "=" * 80)
    print("📊 查看第三章冲突教案的详情")
    print("=" * 80)
    
    for i, plan in enumerate(lesson_plans):
        title = plan.get('title', '未知')
        relevance = plan.get('relevance', 0)
        source = plan.get('source', '')
        filename = Path(source).name if source else '未知'
        
        is_theme_match = plan.get('is_theme_match', False)
        is_conflict = plan.get('is_conflict_theme', False)
        match_evidence = plan.get('match_evidence', [])
        conflict_evidence = plan.get('conflict_evidence', [])
        
        if '3.' in filename and is_conflict:
            print(f"\n📄 {filename}")
            print(f"   相似度: {relevance:.2%}")
            print(f"   主题匹配: {'✅' if is_theme_match else '❌'}")
            print(f"   冲突主题: {'⚠️' if is_conflict else '✅'}")
            
            if conflict_evidence:
                print(f"   冲突证据:")
                for ce in conflict_evidence:
                    conflict_theme, conflict_text = ce
                    print(f"      - {conflict_theme}: {conflict_text}")
            
            metadata = plan.get('metadata', {})
            print(f"   元数据:")
            for key, value in metadata.items():
                if key not in ['content', 'document']:  # 不打印内容，太长了
                    print(f"      - {key}: {value}")
            
            break
    
    print("\n" + "=" * 80)
    print("调试完成！")
    print("=" * 80)


if __name__ == "__main__":
    debug_retrieval()
