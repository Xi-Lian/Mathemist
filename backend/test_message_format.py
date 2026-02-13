from app.graph import create_math_agent_graph
from app.nodes import MathAgentState
import asyncio

async def test_message_format():
    """测试消息格式和重复问题"""
    graph = create_math_agent_graph()
    
    input_state = MathAgentState(
        user_input="帮我查找指数函数相关资源",
        messages=[
            {"role": "user", "content": "帮我查找指数函数相关资源"}
        ]
    )
    
    result = await graph.ainvoke(input_state)
    
    print('====================================')
    print('消息格式分析:')
    print('====================================')
    print(f'消息总数: {len(result.get("messages", []))}')
    print(f'响应内容长度: {len(result.get("response", ""))}')
    
    # 检查消息内容
    messages = result.get("messages", [])
    for i, msg in enumerate(messages):
        print(f'\n消息 {i+1}:')
        print(f'  角色: {msg.get("role")}')
        print(f'  内容长度: {len(msg.get("content", ""))}')
        print(f'  内容预览: {msg.get("content", "")[:100]}...')
    
    print('\n====================================')
    print('响应内容:')
    print('====================================')
    print(result.get("response", ""))

asyncio.run(test_message_format())