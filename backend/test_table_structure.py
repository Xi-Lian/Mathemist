from app.core.resource_table_parser import ResourceTableParser
import json
from pathlib import Path

learning_resource_path = Path(__file__).parent.parent / 'learning_resource'
parser = ResourceTableParser(learning_resource_path)

# 解析习题文件
exercise_file = parser.learning_resource_path / '习题' / '必修一第三章-函数的概念' / '3-3幂函数.md'

with open(exercise_file, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')

# 打印文件的前5行
print("文件内容（前5行）：")
for i, line in enumerate(lines[:5]):
    print(f"{i+1}: {line}")
print()

# 提取表格行（只包含|的行）
table_lines = []
for i, line in enumerate(lines):
    if '|' in line:
        table_lines.append((i+1, line))

print(f"表格行数量: {len(table_lines)}")
print()

# 打印前5个表格行
print("前5个表格行：")
for i, (line_num, line) in enumerate(table_lines[:5]):
    print(f"行 {line_num}: {line}")
