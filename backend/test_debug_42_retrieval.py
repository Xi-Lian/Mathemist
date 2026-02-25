"""
调试4.2指数函数文件的检索过程
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_debug_42_retrieval():
    """调试4.2指数函数的检索过程"""
    print("=" * 80)
    print("调试4.2指数函数文件的检索")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        
        print(f"\n🔍 查找前100条结果中是否有4.2指数函数文件:")
        found_in_top = False
        
        for j, lp in enumerate(lesson_plans[:100]):
            source = lp.get('source', '')
            if '4.2' in source and '指数函数' in source and '4.4' not in source:
                relevance = lp.get('relevance', 0)
                title = lp.get('title', '未知')
                print(f"\n{'=' * 80}")
                print(f"✅ 在第{j+1}位找到4.2指数函数文件!")
                print(f"标题: {title}")
                print(f"文件: {Path(source).name}")
                print(f"相似度: {relevance:.1%}")
                found_in_top = True
        
        if not found_in_top:
            print(f"\n❌ 前100条结果中没有找到4.2指数函数文件!")
            print(f"\n📋 让我们检查它们的向量检索距离...")
            
            # 让我们检查VectorRetriever直接返回的结果
            print(f"\n🔍 检查原始向量检索结果...")
            vector_results = retriever.vector_retriever.retrieve(query, n_results=200)
            
            print(f"\n📊 原始向量检索返回 {len(vector_results)} 条结果")
            
            print(f"\n🔍 在原始向量结果中查找4.2指数函数文件:")
            found_in_vector = False
            
            for j, res in enumerate(vector_results):
                metadata = res.get('metadata', {})
                source_file = metadata.get('source_file', '')
                if '4.2' in source_file and '指数函数' in source_file and '4.4' not in source_file:
                    distance = res.get('distance', 0)
                    relevance = 1 - distance
                    print(f"\n{'=' * 80}")
                    print(f"✅ 在原始向量结果第{j+1}位找到4.2指数函数文件!")
                    print(f"源文件: {source_file}")
                    print(f"距离: {distance:.4f}")
                    print(f"基础相似度: {relevance:.1%}")
                    found_in_vector = True
                    if j >= 20:
                        break
            
            if not found_in_vector:
                print(f"\n❌ 原始向量检索结果中也没有找到4.2指数函数文件!")
                print(f"\n📋 让我们打印前50条原始向量检索结果...")
                for j, res in enumerate(vector_results[:50]):
                    metadata = res.get('metadata', {})
                    source_file = metadata.get('source_file', '')
                    distance = res.get('distance', 0)
                    relevance = 1 - distance
                    print(f"   {j+1:2d}. {Path(source_file).name if source_file else 'N/A'} (距离: {distance:.4f}, 相似度: {relevance:.1%})")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_debug_42_retrieval()
