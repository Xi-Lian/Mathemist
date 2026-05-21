"""
检查概率与统计-课件汇总.xlsx中是否有分步乘法计数原理相关的课件
"""

import pandas as pd
import os

excel_file = r"d:\Git_Repository\Mathemist\learning_resource\概率与统计-课件汇总.xlsx"

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
    
    # 查找包含"分步"、"计数"、"排列"、"组合"的行
    print("查找包含'分步'、'计数'、'排列'、'组合'的行:")
    print("-" * 80)
    
    mask = df.astype(str).apply(lambda x: x.str.contains('分步|计数|排列|组合', case=False, na=False)).any(axis=1)
    matched_rows = df[mask]
    
    print(f"\n找到 {len(matched_rows)} 行匹配:\n")
    
    for idx, row in matched_rows.iterrows():
        print(f"行号: {idx + 2}")  # Excel行号从2开始（第1行是表头）
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                # 移除emoji字符，避免编码错误
                value_str = str(value).replace('✅', '').replace('❌', '')
                print(f"  {col}: {value_str}")
        print()
    
    if len(matched_rows) == 0:
        print("未找到任何相关课件")
        
except Exception as e:
    print(f"读取Excel文件失败: {e}")
    import traceback
    traceback.print_exc()
