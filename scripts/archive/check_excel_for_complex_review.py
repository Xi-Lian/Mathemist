"""
检查立体几何-课件汇总.xlsx中是否有"第七章 复数 章末复习"
"""

import pandas as pd
import os

excel_file = r"d:\Git_Repository\Mathemist\learning_resource\立体几何-课件汇总.xlsx"

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
    
    # 查找包含"复数"或"章末复习"的行
    print("查找包含'复数'或'章末复习'的行:")
    print("-" * 80)
    
    mask = df.astype(str).apply(lambda x: x.str.contains('复数|章末复习', case=False, na=False)).any(axis=1)
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
    
    # 特别查找"章末复习"
    print("\n" + "=" * 80)
    print("特别查找'章末复习':")
    print("-" * 80)
    
    mask_review = df.astype(str).apply(lambda x: x.str.contains('章末复习', case=False, na=False)).any(axis=1)
    review_rows = df[mask_review]
    
    print(f"\n找到 {len(review_rows)} 行包含'章末复习':\n")
    
    for idx, row in review_rows.iterrows():
        print(f"行号: {idx + 2}")
        for col in df.columns:
            value = row[col]
            if pd.notna(value) and str(value).strip():
                # 移除emoji字符，避免编码错误
                value_str = str(value).replace('✅', '').replace('❌', '')
                print(f"  {col}: {value_str}")
        print()
        
except Exception as e:
    print(f"读取Excel文件时出错: {e}")
    import traceback
    traceback.print_exc()
