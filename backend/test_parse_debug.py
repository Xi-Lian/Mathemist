from app.core.resource_table_parser import ResourceTableParser
import json
from pathlib import Path

learning_resource_path = Path(__file__).parent.parent / 'learning_resource'
parser = ResourceTableParser(learning_resource_path)

# 解析习题文件
exercise_file = parser.learning_resource_path / '习题' / '必修一第三章-函数的概念' / '3-3幂函数.md'

with open(exercise_file, 'r', encoding='utf-8') as f:
    content = f.read()

# 手动调用_parse_standard_table函数
lines = content.split('\n')

# 找到表格开始和结束位置
table_start = -1
table_end = -1

for i, line in enumerate(lines):
    # 跳过标题行（以#开头）
    if line.strip().startswith('#'):
        continue
    
    # 检查是否是表格开始行（包含|）
    if '|' in line and table_start == -1:
        table_start = i
    # 检查是否是表格结束行（不包含|且不包含+，且不是空行）
    elif '|' not in line and '+' not in line and table_start != -1:
        # 检查是否是空行（只有空格或完全为空）
        if line.strip() == '':
            # 空行，继续解析
            continue
        # 非空行且不包含|或+，表格结束
        table_end = i
        break

print(f"表格开始位置: {table_start}")
print(f"表格结束位置: {table_end}")
print()

# 提取表格行（只包含|的行）
table_lines = []
for i in range(table_start, table_end):
    line = lines[i]
    if '|' in line:
        table_lines.append(line)

print(f"表格行数量: {len(table_lines)}")
print()

# 检查是否是Excel导出的表格（第一行是标题，第二行是空白/分隔线，第三行是表头）
if len(table_lines) >= 3:
    # 检查文件第一行是否包含".xlsx"（Excel导出的文件通常在第一行有.xlsx文件名）
    # 注意：这里检查的是原始文件的第一行，而不是表格的第一行
    if len(lines) > 0:
        file_first_line = lines[0].strip()
        print(f"文件第一行: {file_first_line}")
        if '.xlsx' in file_first_line or ('Unnamed' in file_first_line):
            # 跳过Excel标题行，保留表头行和数据行
            # 表头行是table_lines[2]，分隔线是table_lines[1]，数据行从table_lines[3]开始
            print("检测到Excel导出的表格，跳过前2行")
            table_lines = table_lines[2:]

print(f"处理后的表格行数量: {len(table_lines)}")
print()

# 解析表头
header_line = table_lines[0]
headers = parser._parse_table_row(header_line)

print(f"表头: {headers}")
print(f"表头数量: {len(headers)}")
print()

# 跳过分隔线（第二行），数据行从第三行开始
data_lines = table_lines[1:] if len(table_lines) > 1 else []

print(f"数据行数量（过滤前）: {len(data_lines)}")
print()

# 过滤掉分隔线行，并合并多行表格单元格
filtered_data_lines = []
for i in range(len(data_lines)):
    line = data_lines[i]
    
    # 检查是否是分隔线（包含:---或类似的模式）
    row = parser._parse_table_row(line)
    is_separator = any(':---' in cell or '---' in cell for cell in row)
    if is_separator:
        print(f"行 {i+1}: 分隔线，跳过")
        continue
    
    # 检查这一行是否是表格行的延续（第一列为空）
    if len(row) > 0 and not row[0].strip() and filtered_data_lines:
        # 这是表格行的延续，合并到上一行
        print(f"行 {i+1}: 表格行的延续，合并到上一行")
        filtered_data_lines[-1] += " " + line.strip()
    else:
        # 这是一个新的表格行
        print(f"行 {i+1}: 新的表格行")
        filtered_data_lines.append(line.strip())

data_lines = filtered_data_lines

print(f"数据行数量（过滤后）: {len(data_lines)}")
print()

# 解析数据行
data = []
for i, line in enumerate(data_lines):
    row = parser._parse_table_row(line)
    
    # 检查是否是分隔线（包含:---或类似的模式）
    is_separator = any(':---' in cell or '---' in cell for cell in row)
    
    # 如果不是分隔线，且列数匹配，则添加到数据中
    if not is_separator:
        # 如果列数不匹配，尝试调整
        if len(row) != len(headers):
            # 如果列数比表头多，且最后一列为空，则去掉最后一列
            if len(row) > len(headers) and not row[-1].strip():
                print(f"行 {i+1}: 列数不匹配（{len(row)} vs {len(headers)}），去掉最后一列")
                row = row[:-1]
            # 如果列数还是不匹配，跳过这一行
            if len(row) != len(headers):
                print(f"行 {i+1}: 列数不匹配（{len(row)} vs {len(headers)}），跳过")
                continue
        
        # 如果列数匹配，则添加到数据中
        if len(row) == len(headers):
            row_dict = {headers[j]: row[j] for j in range(len(headers))}
            data.append(row_dict)
            print(f"行 {i+1}: 成功解析，题目类型: {row_dict.get('题目类型', '')}")

print()
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
