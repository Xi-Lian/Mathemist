import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.graph import create_math_agent_graph
from app.state import MathAgentState

async def test_full_workflow():
    print("=" * 80)
    print("测试完整工作流程")
    print("=" * 80)
    
    try:
        math_agent_graph = create_math_agent_graph()
        
        test_input = "查找指数函数习题"
        
        print(f"\n{'=' * 80}")
        print(f"测试输入: {test_input}")
        print(f"{'=' * 80}")
        
        input_state = MathAgentState(
            user_input=test_input
        )
        
        print(f"\n输入状态: {input_state}")
        
        result = await math_agent_graph.ainvoke(input_state)
        
        print(f"\n{'=' * 80}")
        print(f"最终结果:")
        print(f"{'=' * 80}")
        print(f"  - 意图: {result.get('intent')}")
        print(f"  - 用户需求: {result.get('user_needs')}")
        print(f"  - 资源类型: {result.get('resource_types')}")
        print(f"  - 所有意图: {result.get('intents')}")
        print(f"  - 当前步骤: {result.get('current_step')}")
        
        retrieved_resources = result.get('retrieved_resources', {})
        print(f"\n检索到的资源:")
        for key, value in retrieved_resources.items():
            if value:
                print(f"  - {key}: {len(value)}个")
        
        response = result.get('response', '')
        print(f"\n{'=' * 80}")
        print(f"响应内容（前500字符）:")
        print(f"{'=' * 80}")
        print(response[:500])
        
        print(f"\n{'=' * 80}")
        print(f"响应内容（最后500字符）:")
        print(f"{'=' * 80}")
        print(response[-500:])
        
        print(f"\n{'=' * 80}")
        print("测试完成")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_workflow())
