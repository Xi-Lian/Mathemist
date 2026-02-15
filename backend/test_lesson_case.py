import sys
import os
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.graph import create_math_agent_graph
from app.state import MathAgentState

async def test_lesson_case_retrieval():
    print("=" * 80)
    print("测试课例检索")
    print("=" * 80)
    
    try:
        math_agent_graph = create_math_agent_graph()
        
        test_input = "查找指数函数的课件和课例"
        
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
        print(f"响应内容（前1000字符）:")
        print(f"{'=' * 80}")
        print(response[:1000])
        
        print(f"\n{'=' * 80}")
        print(f"响应内容（课例部分）:")
        print(f"{'=' * 80}")
        if "课例" in response:
            start = response.find("【课例资源】")
            if start != -1:
                end = response.find("\n\n\n", start)
                if end == -1:
                    end = len(response)
                print(response[start:end])
        else:
            print("响应中没有找到课例资源")
        
        print(f"\n{'=' * 80}")
        print("测试完成")
        print(f"{'=' * 80}")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_lesson_case_retrieval())
