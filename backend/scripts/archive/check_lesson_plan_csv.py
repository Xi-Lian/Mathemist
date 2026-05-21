#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查立体几何教案资源汇总表CSV文件的内容
"""

import sys
import os
import pandas as pd

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

if __name__ == "__main__":
    print("\n" + "="*60)
    print("详细检查立体几何教案资源汇总表CSV文件")
    print("="*60)

    # 读取CSV文件
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'learning_resource', '立体几何-教案资源信息汇总表.csv')

    print(f"\n读取CSV文件: {csv_path}")

    try:
        # 尝试不同编码
        df = None
        for encoding in ['utf-8', 'gbk', 'gb2312', 'gb18030']:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                print(f"成功使用编码: {encoding}")
                break
            except:
                continue

        if df is None:
            print("无法读取CSV文件")
        else:
            print(f"\nCSV文件列名: {df.columns.tolist()}")
            print(f"CSV文件总行数: {len(df)}")

            # 检查文件名包含"复数"的行
            if '文件名' in df.columns:
                print(f"\n文件名包含'复数'的行数: {df['文件名'].str.contains('复数', na=False).sum()}")

                # 显示前10个文件名包含"复数"的行
                complex_rows = df[df['文件名'].str.contains('复数', na=False)]
                print(f"\n前10个文件名包含'复数'的示例：")
                for i, row in complex_rows.head(10).iterrows():
                    print(f"  {i+1}. {row['文件名']}")

                # 检查文件扩展名
                print(f"\n文件名包含'复数'的文件扩展名分布：")
                ext_counts = complex_rows['文件名'].apply(lambda x: os.path.splitext(x)[1] if pd.notna(x) else '未知').value_counts()
                for ext, count in ext_counts.items():
                    print(f"  - {ext}: {count}条")

            # 检查是否有图片列
            if '图片名称' in df.columns:
                print(f"\n图片名称列:")
                print(f"  总数: {df['图片名称'].notna().sum()}")
                print(f"  文件名包含'复数'的图片: {df[df['图片名称'].str.contains('复数', na=False)]['图片名称'].count()}")

                # 显示前5个图片名称
                complex_images = df[df['图片名称'].str.contains('复数', na=False)]['图片名称']
                print(f"\n前5个文件名包含'复数'的图片：")
                for i, img in enumerate(complex_images.head(5)):
                    print(f"  {i+1}. {img}")

    except Exception as e:
        print(f"读取CSV文件出错: {e}")

    print("\n" + "="*60)
    print("检查完成")
    print("="*60)
