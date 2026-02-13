from app.graph import create_math_agent_graph
from app.state import MathAgentState
import asyncio

async def test_full_flow():
    # 创建图
    graph = create_math_agent_graph()
    
    # 创建输入状态
    input_state = MathAgentState(
        user_input="帮我查找指数函数相关资源",
        messages=[
            {"role": "user", "content": "帮我查找指数函数相关资源"}
        ]
    )
    
    print("====================================")
    print("开始测试完整流程")
    print("====================================")
    print(f"输入: {input_state.user_input}")
    print(f"消息: {input_state.messages}")
    print()
    
    # 调用图
    result = await graph.ainvoke(input_state)
    
    print()
    print("====================================")
    print("流程完成")
    print("====================================")
    print(f"结果类型: {type(result)}")
    print(f"意图: {result.get('intent')}")
    print(f"所有意图: {result.get('intents')}")
    print(f"当前步骤: {result.get('current_step')}")
    print(f"错误: {result.get('error')}")
    print(f"响应: {result.get('response')}")
    print(f"消息数量: {len(result.get('messages', []))}")
    
    if result.get('messages'):
        print()
        print("====================================")
        print("消息列表:")
        print("====================================")
        for i, msg in enumerate(result.get('messages', [])):
            print(f"{i+1}. {msg.get('role')}: {msg.get('content')[:100]}...")

# 运行测试
asyncio.run(test_full_flow())
