from app.nodes import retrieve_resources

# 测试检索指数函数相关资源
result = retrieve_resources('指数函数', 'search')

print('====================================')
print('检索结果详细分析:')
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

print('\n====================================')
print('教案资源详情:')
print('====================================')
for i, r in enumerate(result["lesson_plan_patterns"]):
    print(f'{i+1}. {r["title"]}')
    print(f'   相似度: {r["relevance"]:.2f}')
    print(f'   路径: {r["source"]}')
    print()

print('====================================')
print('习题资源详情:')
print('====================================')
for i, r in enumerate(result["exercise_resources"]):
    print(f'{i+1}. {r["title"]}')
    print(f'   相似度: {r["relevance"]:.2f}')
    print(f'   路径: {r["source"]}')
    print()
