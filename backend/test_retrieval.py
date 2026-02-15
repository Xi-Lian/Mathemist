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
        
        test_input = "查找指数函数的课件和课例"
        
        print(f"\n{'=' * 80}")
        print(f"测试输入: {test_input}")
        print(f"{'=' * 80}")
        
        # 测试不指定资源类型的检索
        print("\n--- 测试1：不指定资源类型 ---")
        result1 = retriever.retrieve(test_input, intent="search", resource_types=None)
        
        print(f"\n检索到的资源:")
        for key, value in result1.items():
            if value:
                print(f"  - {key}: {len(value)}个")
        
        # 测试指定课件和课例类型的检索
        print("\n--- 测试2：指定资源类型为['课件', '课例'] ---")
        result2 = retriever.retrieve(test_input, intent="search", resource_types=['课件', '课例'])
        
        print(f"\n检索到的资源:")
        for key, value in result2.items():
            if value:
                print(f"  - {key}: {len(value)}个")
        
        # 测试只指定课例类型的检索
        print("\n--- 测试3：只指定资源类型为['课例'] ---")
        result3 = retriever.retrieve(test_input, intent="search", resource_types=['课例'])
        
        print(f"\n检索到的资源:")
        for key, value in result3.items():
            if value:
                print(f"  - {key}: {len(value)}个")
        
        # 测试只指定课件类型的检索
        print("\n--- 测试4：只指定资源类型为['课件'] ---")
        result4 = retriever.retrieve(test_input, intent="search", resource_types=['课件'])
        
        print(f"\n检索到的资源:")
        for key, value in result4.items():
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
