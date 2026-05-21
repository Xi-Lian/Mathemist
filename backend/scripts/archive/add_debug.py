import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 添加调试日志
old_pattern = '''        # 检测是否为分别查询
        user_input = self._get_state_value(state, "user_input", "")
        is_separate_query = any(keyword in user_input for keyword in ["分别", "各自", "分开"])

        # 检测是否为多主题查询
        has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及", "、"])

        if is_separate_query and has_multi_themes:
            # 分别查询模式：按主题分组显示资源
            print(f"📋 检测到分别查询，按主题分组显示资源")'''

new_pattern = '''        # 检测是否为分别查询
        user_input = self._get_state_value(state, "user_input", "")
        print(f"DEBUG: user_input = {user_input}")
        is_separate_query = any(keyword in user_input for keyword in ["分别", "各自", "分开"])
        print(f"DEBUG: is_separate_query = {is_separate_query}")

        # 检测是否为多主题查询
        has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及", "、"])
        print(f"DEBUG: has_multi_themes = {has_multi_themes}")

        if is_separate_query and has_multi_themes:
            # 分别查询模式：按主题分组显示资源
            print(f"检测到分别查询，按主题分组显示资源")

            # 按主题分组资源
            theme_resources = {}
            for resource in filtered_resources:
                # 获取资源匹配的主题
                matched_themes = resource.get("matched_themes", [])
                print(f"DEBUG: resource matched_themes = {matched_themes}")
                if not matched_themes:
                    print(f"DEBUG: resource has no matched_themes, skipping")
                    continue'''

new_content = content.replace(old_pattern, new_pattern)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("文件修改完成！")