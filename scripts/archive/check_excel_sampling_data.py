"""
检查概率与统计-课例视频.xlsx的实际内容
"""

import pandas as pd
import os

excel_file = r"d:\Git_Repository\Mathemist\learning_resource\概率与统计-课例视频.xlsx"

if not os.path.exists(excel_file):
    print(f"文件不存在: {excel_file}")
    exit(1)

print("=" * 80)
print(f"检查文件: {excel_file}")
print("=" * 80)

try:
    # 读取Excel文件
    df = pd.read_excel(excel_file)
    
    print(f"\n总行数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    print()
    
    # 查找包含"抽样"的行
    mask = df.astype(str).apply(lambda x: x.str.contains('抽样', case=False, na=False)).any(axis=1)
    matching_rows = df[mask]
    
    print(f"找到 {len(matching_rows)} 行包含'抽样'的记录:\n")
    
    for idx, row in matching_rows.iterrows():
        print(f"行号: {idx + 2}")
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                value_str = str(value)[:100]  # 限制长度
                print(f"  {col}: {value_str}")
        print()
        
except Exception as e:
    print(f"读取Excel文件失败: {e}")
    import traceback
    traceback.print_exc()
