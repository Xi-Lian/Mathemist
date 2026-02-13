from app.nodes import retrieve_resources, search_result_processing_node
from app.state import MathAgentState

# 检索资源
result = retrieve_resources('指数函数', 'search')

# 创建状态
state = MathAgentState(
    user_input='指数函数',
    retrieved_resources=result,
    current_step='search_result_processing'
)

# 处理搜索结果
processed = search_result_processing_node(state)

print('====================================')
print('搜索结果处理输出:')
print('====================================')
print(processed.get('search_results', '无结果'))
print('\n====================================')
print('处理状态:')
print('====================================')
print(f'当前步骤: {processed.get("current_step", "未知")}')
print(f'错误信息: {processed.get("error", "无错误")}')
