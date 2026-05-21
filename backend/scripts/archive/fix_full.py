import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找并替换整个if-else块
old_pattern = r'''
        # V314.0实现：分别查询时拆分为多个单主题查询
        if is_separate_query and is_multi_theme_query:
            print\("V314.0检测到分别查询，将多主题查询拆分为多个单主题查询..."\)

            # 提取各个主题
            themes = _extract_themes_from_query\(original_user_query or tool_args\.get\("query", ""\)\)
            print\(f"V314.0提取到的主题: \{themes\}"\)

            # 获取资源类型
            resource_types = tool_args\.get\("resource_types", \[\]\)

            # 为每个主题分别执行单主题查询
            for theme_idx, theme in enumerate\(themes\):
                theme_query = f"\{theme\} \{resource_types\[0\]\}" if resource_types else theme
                print\(f"V314.0 执行单主题查询\[\{theme_idx\+1\}/\{len\(themes\)\}\]: '\{theme_query\}'"\)

                # 创建单主题工具参数
                single_theme_args = \{
                    "query": theme_query,
                    "queries": \[theme_query\],
                    "resource_types": resource_types
                \}

                # 执行单主题查询
                tool_result = search_tool\.invoke\(single_theme_args\)
                try:
                    parsed = json\.loads\(tool_result\)
                except Exception:
                    parsed = \{\}

                if isinstance\(parsed, dict\):
                    candidate_resources = parsed\.get\("retrieved_resources"\)
                    candidate_count = count_retrieved_resources\(candidate_resources\)
                    print\(f"   V314.0 单主题查询'\{theme\}'返回资源总数: \{candidate_count\}"\)

                    if isinstance\(candidate_resources, dict\) and candidate_count > 0:
                        all_resource_groups\.append\(candidate_resources\)
        else:
            # 并行处理查询变体的检索
            if tool_args\.get\("queries"\) and len\(tool_args\.get\("queries", \[\]\)\) > 1:
                print\(f"并行处理 \{len\(tool_args\.get\('queries', \[\]\)\) \} 个查询变体"\)

                # 为每个查询变体创建单独的工具参数
                query_args_list = \[\]
                for query_variant in tool_args\.get\("queries", \[\]\):
                    variant_args = tool_args\.copy\(\)
                    variant_args\["query"\] = query_variant
                    variant_args\["queries"\] = \[query_variant\]  # 每个变体单独检索
                    query_args_list\.append\(variant_args\)

                # 并行执行所有查询变体
                results = asyncio\.run\(_parallel_invoke\(search_tool, query_args_list\)\)

                # 处理并行结果
                for i, \(variant_result, variant_args\) in enumerate\(zip\(results, query_args_list\)\):
                    try:
                        parsed = json\.loads\(variant_result\)
                    except Exception:
                        parsed = \{\}
                    if isinstance\(parsed, dict\):
                        candidate_resources = parsed\.get\("retrieved_resources"\)
                        candidate_count = count_retrieved_resources\(candidate_resources\)
                        print\(f"   并行查询\[\{i\+1\}\] '\{variant_args\.get\('query', ''\)\}' 返回资源总数: \{candidate_count\}"\)
                        if isinstance\(candidate_resources, dict\):
                            all_resource_groups\.append\(candidate_resources\)
                            if candidate_count > best_result_count:
                                best_result_count = candidate_count
                                print\(f"   并行查询\[\{i\+1\}\] 成为当前最佳结果"\)
                                response_text = build_search_response_payload\(
                                    query=original_user_query or variant_args\.get\("query", ""\) or "",
                                    resource_types=variant_args\.get\("resource_types", \[\]\),
                                    retrieved_resources=candidate_resources,
                                \)\.strip\(\)
                    else:
                        print\(f"   并行查询\[\{i\+1\}\] 未返回有效结果"\)
            else:
                # 单查询变体，使用传统方式
                tool_result = search_tool\.invoke\(tool_args\)
                try:
                    parsed = json\.loads\(tool_result\)
                except Exception:
                    parsed = \{\}
                if isinstance\(parsed, dict\):
                    candidate_resources = parsed\.get\("retrieved_resources"\)
                    candidate_count = count_retrieved_resources\(candidate_resources\)
                    print\(f"   ↳ 工具调用\[\{idx\}\] 返回资源总数: \{candidate_count\}"\)
                    if isinstance\(candidate_resources, dict\):
                        all_resource_groups\.append\(candidate_resources\)
                        if candidate_count > best_result_count:
                            best_result_count = candidate_count
                            print\(f"   工具调用\[\{idx\}\] 成为当前最佳结果"\)
                            response_text = build_search_response_payload\(
                                query=original_user_query or tool_args\.get\("query", ""\) or "",
                                resource_types=tool_args\.get\("resource_types", \[\]\),
                                retrieved_resources=candidate_resources,
                            \)\.strip\(\)
                    else:
                        print\(f"   工具调用\[\{idx\}\] 未超过当前最佳结果数 \{best_result_count\}\)'''

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
            # 并行处理查询变体的检索
            if tool_args.get("queries") and len(tool_args.get("queries", [])) > 1:
                print(f"并行处理 {len(tool_args.get('queries', []))} 个查询变体")

                # 为每个查询变体创建单独的工具参数
                query_args_list = []
                for query_variant in tool_args.get("queries", []):
                    variant_args = tool_args.copy()
                    variant_args["query"] = query_variant
                    variant_args["queries"] = [query_variant]  # 每个变体单独检索
                    query_args_list.append(variant_args)

                # 并行执行所有查询变体
                results = asyncio.run(_parallel_invoke(search_tool, query_args_list))

                # 处理并行结果
                for i, (variant_result, variant_args) in enumerate(zip(results, query_args_list)):
                    try:
                        parsed = json.loads(variant_result)
                    except Exception:
                        parsed = {}
                    if isinstance(parsed, dict):
                        candidate_resources = parsed.get("retrieved_resources")
                        candidate_count = count_retrieved_resources(candidate_resources)
                        print(f"   并行查询[{i+1}] '{variant_args.get('query', '')}' 返回资源总数: {candidate_count}")
                        if isinstance(candidate_resources, dict):
                            all_resource_groups.append(candidate_resources)
                            if candidate_count > best_result_count:
                                best_result_count = candidate_count
                                print(f"   并行查询[{i+1}] 成为当前最佳结果")
                                response_text = build_search_response_payload(
                                    query=original_user_query or variant_args.get("query", "") or "",
                                    resource_types=variant_args.get("resource_types", []),
                                    retrieved_resources=candidate_resources,
                                ).strip()
                    else:
                        print(f"   并行查询[{i+1}] 未返回有效结果")
            else:
                # 单查询变体，使用传统方式
                tool_result = search_tool.invoke(tool_args)
                try:
                    parsed = json.loads(tool_result)
                except Exception:
                    parsed = {}
                if isinstance(parsed, dict):
                    candidate_resources = parsed.get("retrieved_resources")
                    candidate_count = count_retrieved_resources(candidate_resources)
                    print(f"   工具调用[{idx}] 返回资源总数: {candidate_count}")
                    if isinstance(candidate_resources, dict):
                        all_resource_groups.append(candidate_resources)
                        if candidate_count > best_result_count:
                            best_result_count = candidate_count
                            print(f"   工具调用[{idx}] 成为当前最佳结果")
                            response_text = build_search_response_payload(
                                query=original_user_query or tool_args.get("query", "") or "",
                                resource_types=tool_args.get("resource_types", []),
                                retrieved_resources=candidate_resources,
                            ).strip()
                    else:
                        print(f"   工具调用[{idx}] 未超过当前最佳结果数 {best_result_count}")'''

# 由于原内容中包含特殊字符，使用更简单的字符串替换方法
# 先找到替换的起始位置
start_marker = '        # V314.0实现：分别查询时拆分为多个单主题查询'
end_marker = '    # 合并所有工具调用的结果'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx == -1:
    print("未找到起始标记")
    exit(1)
if end_idx == -1:
    print("未找到结束标记")
    exit(1)

print(f"找到替换范围: {start_idx} - {end_idx}")

# 替换内容
new_content = content[:start_idx] + new_code + content[end_idx:]

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("文件替换完成！")