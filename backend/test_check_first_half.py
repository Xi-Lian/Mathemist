"""
检查教案的前半部分
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from app.core.resource_retriever import ResourceRetriever


def test_check_first_half():
    """检查教案的前半部分"""
    print("=" * 80)
    print("检查教案的前半部分")
    print("=" * 80)
    
    query = "推送指数函数的概念教学设计资源"
    print(f"\n📝 用户查询: {query}")
    
    retriever = ResourceRetriever()
    
    try:
        print(f"\n🔍 开始检索...")
        results = retriever.retrieve(query, intent="search")
        
        lesson_plans = results.get("lesson_plan_patterns", [])
        
        print(f"\n📊 总教案数: {len(lesson_plans)}条")
        
        half = len(lesson_plans) // 2
        print(f"\n📋 检查前 {half} 个教案...")
        
        found = False
        for j, lp in enumerate(lesson_plans[:half]):
            source = lp.get('source', '')
            relevance = lp.get('relevance', 0)
            filename = Path(source).name if source else '未知'
            print(f"{j+1:3d}. {filename} (相似度: {relevance:.1%})")
            
            if '4.2' in source and '指数函数' in source and '4.4' not in source:
                print(f"\n✅ 找到4.2指数函数文件在第{j+1}位!")
                found = True
        
        if not found:
            print(f"\n❌ 前{half}个教案中没有找到4.2指数函数文件!")
            print(f"\n📋 检查后{half}个教案...")
            
            for j, lp in enumerate(lesson_plans[half:]):
                source = lp.get('source', '')
                if '4.2' in source and '指数函数' in source and '4.4' not in source:
                    relevance = lp.get('relevance', 0)
                    filename = Path(source).name if source else '未知'
                    print(f"{half + j + 1:3d}. {filename} (相似度: {relevance:.1%})")
                    found = True
        
        if not found:
            print(f"\n❌ 所有教案中都没有找到4.2指数函数文件!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_check_first_half()
