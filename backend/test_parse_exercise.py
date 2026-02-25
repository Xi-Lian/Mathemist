from app.core.resource_table_parser import ResourceTableParser
import json
from pathlib import Path

learning_resource_path = Path(__file__).parent.parent / 'learning_resource'
parser = ResourceTableParser(learning_resource_path)

# 解析习题文件
exercise_file = parser.learning_resource_path / '习题' / '必修一第三章-函数的概念' / '3-3幂函数.md'

with open(exercise_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 打印文件的前20行
print("文件内容（前20行）：")
lines = content.split('\n')
for i, line in enumerate(lines[:20]):
    print(f"{i+1}: {line}")
print()

# 打印文件的第3-8行（表格部分）
print("文件内容（第3-8行）：")
for i, line in enumerate(lines[2:8]):
    print(f"{i+3}: {line}")
print()

data = parser.parse_markdown_table(content)

print(f"解析到 {len(data)} 条记录")
print()

# 打印前5条记录的详细信息
for i, item in enumerate(data[:5]):
    print(f"记录 {i+1}:")
    print(f"  题目类型: {item.get('题目类型', '')}")
    print(f"  题干: {item.get('题干', '')[:100] if item.get('题干') else '(空)'}...")
    print(f"  知识点标签: {item.get('知识点标签', '')}")
    print(f"  解析: {item.get('解析', '')[:100] if item.get('解析') else '(空)'}...")
    print(f"  题目文件名: {item.get('题目文件名', '')}")
    print()
