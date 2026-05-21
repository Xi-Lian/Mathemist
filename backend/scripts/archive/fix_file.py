import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 查找问题代码并修复
# 需要将 "        else:\n        # 并行处理查询变体的检索" 
# 修改为 "        else:\n            # 并行处理查询变体的检索"
old_pattern = r'        else:\n        # 并行处理查询变体的检索'
new_pattern = '        else:\n            # 并行处理查询变体的检索'

new_content = content.replace(old_pattern, new_pattern)

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("文件修复完成！")