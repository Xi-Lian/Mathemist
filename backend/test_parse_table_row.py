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

# 打印表格的第4-6行（数据行）
print("表格的第4-6行（数据行）：")
for i in range(3, 6):
    line = lines[i]
    print(f"行 {i+1}: {line}")
    row = parser._parse_table_row(line)
    print(f"  解析后的单元格数量: {len(row)}")
    for j, cell in enumerate(row):
        print(f"    单元格 {j+1}: {cell[:50] if cell else '(空)'}...")
    print()
