"""
详细调试 parse_standard_table 的解析过程
"""
import sys
sys.path.insert(0, 'backend')

from pathlib import Path

# 读取测试文件
with open('temp_3-2-1.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("=" * 80)
print("详细分析 temp_3-2-1.md 的每一行")
print("=" * 80)

for i, line in enumerate(lines, 1):
    has_pipe = '|' in line
    is_empty = line.strip() == ''
    starts_with_hash = line.strip().startswith('#')
    
    status = []
    if starts_with_hash:
        status.append("标题行")
    elif is_empty:
        status.append("空行")
    elif has_pipe:
        status.append("表格行 ✅")
    else:
        status.append("非表格行 ❌")
    
    # 显示前80个字符
    preview = line.rstrip()[:80]
    if len(line.rstrip()) > 80:
        preview += "..."
    
    print(f"第{i:2d}行 [{', '.join(status)}]: {preview}")

print("\n" + "=" * 80)
print("统计:")
print(f"  总行数: {len(lines)}")
print(f"  表格行数量: {sum(1 for line in lines if '|' in line)}")
print(f"  空行数量: {sum(1 for line in lines if line.strip() == '')}")
print("=" * 80)
