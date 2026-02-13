from app.nodes import search_result_processing_node
from app.nodes import MathAgentState

# 创建测试状态，包含图片题目和文字题目
state = MathAgentState(
    user_input="帮我查找指数函数相关资源",
    retrieved_resources={
        "exercise_resources": [
            {
                "title": "指数函数习题1",
                "content": "指数函数练习题",
                "source": "D:/test/习题1.md",
                "relevance": 0.80
            },
            {
                "title": "指数函数图象及性质的应用",
                "content": "| 题目文件 | 4-2-2指数函数图象及性质的应用答案1.png |",
                "source": "D:/test/习题2.md",
                "relevance": 0.85
            }
        ]
    }
)

# 测试搜索结果处理
try:
    result = search_result_processing_node(state)
    print('====================================')
    print('习题资源显示测试结果:')
    print('====================================')
    print(f'处理状态: {result.get("current_step")}')
    print(f'错误信息: {result.get("error")}')
    print('\n====================================')
    print('搜索结果:')
    print('====================================')
    print(result.get("search_results"))
    print('\n====================================')
    print('测试完成!')
    print('====================================')
except Exception as e:
    print(f'测试失败: {str(e)}')