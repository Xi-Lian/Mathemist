"""
简单检查所有教案结果
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_simple_check():
    """简单检查"""
    print("=" * 80)
    print("简单检查所有教案结果")
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
            if '4.2' in source and '指数函数' in source and '4.4' not in source:
                relevance = lp.get('relevance', 0)
                print(f"✅ 第{j+1}位: {source} (相似度: {relevance:.1%})")
                found = True
        
        if not found:
            print(f"\n❌ 未找到4.2指数函数文件!")
            print(f"\n📄 打印所有教案的路径:")
            for j, lp in enumerate(lesson_plans):
                source = lp.get('source', '')
                relevance = lp.get('relevance', 0)
                print(f"{j+1:3d}. {source} (相似度: {relevance:.1%})")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_simple_check()
