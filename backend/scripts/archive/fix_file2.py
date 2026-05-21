import re

# 读取文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# 找到问题行并修复
for i, line in enumerate(lines):
    if line == '        # 并行处理查询变体的检索\n':
        lines[i] = '            # 并行处理查询变体的检索\n'
        print(f"修复第{i+1}行")
        break

# 写回文件
with open('d:/Git_Repository/Mathemist/backend/app/search_agent_runtime.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("修复完成！")