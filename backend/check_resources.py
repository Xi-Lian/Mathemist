from app.nodes import retrieve_resources

result = retrieve_resources('指数函数', 'search')
print('检索到的资源类型:')
print(f'理论资源: {len(result["theory_resources"])}条')
print(f'教案: {len(result["lesson_plan_patterns"])}条')
print(f'习题: {len(result["exercise_resources"])}条')
print(f'可视化: {len(result["visualization_examples"])}条')
print(f'通用: {len(result["general_resources"])}条')
print(f'课件: {len(result["courseware_resources"])}条')
print(f'课例: {len(result["lesson_case_resources"])}条')
print(f'GGB: {len(result["ggb_resources"])}条')
print(f'教学大纲: {len(result["syllabus_resources"])}条')

print('\n详细资源列表:')
for key, resources in result.items():
    if resources:
        print(f'\n{key}:')
        for r in resources[:3]:
            print(f'  - {r.get("title", "无标题")}')
            print(f'    来源: {r.get("source", "")}')
