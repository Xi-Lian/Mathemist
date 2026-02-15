import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.resource_retriever import ResourceRetriever

async def test_retrieval():
    print("=" * 80)
    print("测试资源检索")
    print("=" * 80)
    
    try:
        retriever = ResourceRetriever()
        
        test_queries = [
            ("查找指数函数的课件和课例", ['课件', '课例']),
            ("查找指数函数课例", ['课例']),
            ("查找指数函数课件", ['课件']),
            ("查找指数函数习题", ['习题'])
        ]
        
        for query, resource_types in test_queries:
            print(f"\n{'=' * 80}")
            print(f"查询: {query}")
            print(f"资源类型: {resource_types}")
            print(f"{'=' * 80}")
            
            result = retriever.retrieve(query, intent="search", resource_types=resource_types)
            
            print(f"\n检索到的资源:")
            for key, value in result.items():
                if value:
                    print(f"  - {key}: {len(value)}个")
        
        print(f"\n{'=' * 80}")
        print("测试完成")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_retrieval())
