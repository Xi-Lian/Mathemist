import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到需要修改的位置
# 在 "print(f"执行工具调用...)" 之后， "# 并行处理查询变体的检索" 之前插入新代码
target_line = '        # 并行处理查询变体的检索\n'

# 找到这行的索引
insert_idx = None
for i, line in enumerate(lines):
    if line == target_line:
        insert_idx = i
        break

if insert_idx is None:
    print(f"未找到目标行: {repr(target_line)}")
    exit(1)

print(f"找到目标行，索引: {insert_idx}")

# 要插入的新代码
new_code = '''
        # V314.0实现：分别查询时拆分为多个单主题查询
        if is_separate_query and is_multi_theme_query:
            print("V314.0检测到分别查询，将多主题查询拆分为多个单主题查询...")

            # 提取各个主题
            themes = _extract_themes_from_query(original_user_query or tool_args.get("query", ""))
            print(f"V314.0提取到的主题: {themes}")

            # 获取资源类型
            resource_types = tool_args.get("resource_types", [])

            # 为每个主题分别执行单主题查询
            for theme_idx, theme in enumerate(themes):
                theme_query = f"{theme} {resource_types[0]}" if resource_types else theme
                print(f"V314.0 执行单主题查询[{theme_idx+1}/{len(themes)}]: '{theme_query}'")

                # 创建单主题工具参数
                single_theme_args = {
                    "query": theme_query,
                    "queries": [theme_query],
                    "resource_types": resource_types
                }

                # 执行单主题查询
                tool_result = search_tool.invoke(single_theme_args)
                try:
                    parsed = json.loads(tool_result)
                except Exception:
                    parsed = {}

                if isinstance(parsed, dict):
                    candidate_resources = parsed.get("retrieved_resources")
                    candidate_count = count_retrieved_resources(candidate_resources)
                    print(f"   V314.0 单主题查询'{theme}'返回资源总数: {candidate_count}")

                    if isinstance(candidate_resources, dict) and candidate_count > 0:
                        all_resource_groups.append(candidate_resources)
        else:
'''

# 插入新代码
lines.insert(insert_idx, new_code)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("文件修改完成！")