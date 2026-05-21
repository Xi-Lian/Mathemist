import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换has_multi_themes的检测逻辑，加入顿号"、"的检测
old_pattern = 'has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及"])'
new_pattern = 'has_multi_themes = any(keyword in user_input for keyword in ["和", "与", "及", "还有", "以及", "、"])'

new_content = content.replace(old_pattern, new_pattern)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/core/response/methods/format_resource_category.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("文件修改完成！")