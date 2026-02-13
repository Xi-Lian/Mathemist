from app.nodes import retrieve_resources, search_result_processing_node
from app.state import MathAgentState

# 检索资源
result = retrieve_resources('指数函数', 'search')

print('====================================')
print('检索到的资源:')
print('====================================')
print(f'理论资源: {len(result["theory_resources"])}条')
print(f'教案: {len(result["lesson_plan_patterns"])}条')
print(f'习题: {len(result["exercise_resources"])}条')
print(f'可视化: {len(result["visualization_examples"])}条')
print(f'通用: {len(result["general_resources"])}条')
print(f'课件: {len(result["courseware_resources"])}条')
print(f'课例: {len(result["lesson_case_resources"])}条')
print(f'GGB: {len(result["ggb_resources"])}条')
print(f'教学大纲: {len(result["syllabus_resources"])}条')

# 创建状态
state = MathAgentState(
    user_input='指数函数',
    retrieved_resources=result,
    current_step='search_result_processing'
)

# 处理搜索结果
processed = search_result_processing_node(state)

print('\n====================================')
print('搜索结果处理输出:')
print('====================================')
print(processed.get('search_results', '无结果'))
