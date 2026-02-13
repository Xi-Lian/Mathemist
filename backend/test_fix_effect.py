from app.nodes import search_result_processing_node
from app.nodes import MathAgentState

# 创建测试状态
state = MathAgentState(
    user_input="帮我查找指数函数相关资源",
    retrieved_resources={
        "lesson_plan_patterns": [
            {
                "title": "指数函数教案1",
                "content": "指数函数的概念和性质",
                "source": "D:/test/教案1.md",
                "relevance": 0.85
            },
            {
                "title": "指数函数教案2", 
                "content": "指数函数图象分析",
                "source": "D:/test/教案2.md",
                "relevance": 0.75
            },
            {
                "title": "指数函数教案1",  # 重复资源
                "content": "指数函数的概念和性质",
                "source": "D:/test/教案1.md",
                "relevance": 0.85
            }
        ],
        "exercise_resources": [
            {
                "title": "指数函数习题1",
                "content": "指数函数练习题",
                "source": "D:/test/习题1.md",
                "relevance": 0.80
            }
        ],
        "syllabus_resources": [
            {
                "title": "函数教学大纲",
                "content": "包含指数函数教学要求",
                "source": "D:/test/教学大纲.md",
                "relevance": 0.70
            }
        ]
    }
)

# 测试搜索结果处理
try:
    result = search_result_processing_node(state)
    print('====================================')
    print('测试结果:')
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