import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换整个分别查询模式的判断逻辑
old_pattern = '''        # 检测是否为分别查询
        user_input = self._get_state_value(state, "user_input", "")
        is_separate_query = any(keyword in user_input for keyword in ["分别", "各自", "分开"])
        
        # 检测是否为多主题查询
        has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及", "、"])
        
        if is_separate_query and has_multi_themes:
            # 分别查询模式：按主题分组显示资源
            print(f"📋 检测到分别查询，按主题分组显示资源")
            
            # 按主题分组资源
            theme_resources = {}
            for resource in filtered_resources:
                # 获取资源匹配的主题
                matched_themes = resource.get("matched_themes", [])
                if not matched_themes:
                    continue
                
                for theme in matched_themes:
                    if theme not in theme_resources:
                        theme_resources[theme] = []
                    theme_resources[theme].append(resource)
            
            # 对每个主题的资源进行排序
            for theme, theme_items in theme_resources.items():
                # 按相关性排序
                theme_items.sort(key=lambda x: (-x.get('relevance', 0), -x.get('is_core_match', False)))
                
                # 显示该主题的资源
                response_parts.append(f"\n📋 【主题：{theme}】（{len(theme_items)}个）：\n")
                
                # 每个主题最多显示5个资源
                for resource in theme_items[:5]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        else:'''

new_pattern = '''        # 检测是否为分别查询（简化判断：只检查是否包含"分别"或"各自"）
        user_input = self._get_state_value(state, "user_input", "")
        is_separate_query = any(keyword in user_input for keyword in ["分别", "各自", "分开"])

        # V315.0: 分别查询模式时，按主题分组显示资源
        if is_separate_query:
            print(f"[DEBUG] 进入分别查询模式，user_input='{user_input}'")
            print(f"[DEBUG] filtered_resources数量={len(filtered_resources)}")

            # 按主题分组资源
            theme_resources = {}
            for resource in filtered_resources:
                # 获取资源匹配的主题
                matched_themes = resource.get("matched_themes", [])
                print(f"[DEBUG] 资源title={resource.get('meta', {}).get('title', 'unknown')[:30]}, matched_themes={matched_themes}")
                if not matched_themes:
                    print(f"[DEBUG] 资源没有matched_themes，跳过")
                    continue

                for theme in matched_themes:
                    if theme not in theme_resources:
                        theme_resources[theme] = []
                    theme_resources[theme].append(resource)

            print(f"[DEBUG] theme_resources数量={len(theme_resources)}, 内容={list(theme_resources.keys())}")

            # 对每个主题的资源进行排序
            for theme, theme_items in theme_resources.items():
                # 按相关性排序
                theme_items.sort(key=lambda x: (-x.get('relevance', 0), -x.get('is_core_match', False)))

                # 显示该主题的资源
                response_parts.append(f"\n【{theme}】相关资源（{len(theme_items)}个）：\n")

                # 每个主题最多显示5个资源
                for resource in theme_items[:5]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        else:'''

new_content = content.replace(old_pattern, new_pattern)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("文件修改完成！")