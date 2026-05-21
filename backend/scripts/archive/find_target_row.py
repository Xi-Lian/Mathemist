import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import csv

def find_target_row():
    """
    在概率教案索引中查找目标教案
    """
    # 列出learning_resource目录中的CSV文件
    lr_dir = r"D:\Git_Repository\Mathemist\learning_resource"
    csv_files = [f for f in os.listdir(lr_dir) if f.endswith('.csv')]
    print(f"CSV文件: {csv_files}")

    for csv_file in csv_files:
        filepath = os.path.join(lr_dir, csv_file)
        print(f"\n检查: {csv_file}")

        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row.get('文件名', '')
                    if '3310' in filename:
                        print(f"\n找到目标!")
                        print(f"文件名: {filename}")
                        print(f"云端链接: {row.get('云端链接', '')}")
                        print(f"扩展名: {row.get('扩展名', '')}")
                        print(f"文件类型: {row.get('文件类型', '')}")
                        print(f"关联文件: {row.get('关联文件', '')}")
                        return
        except Exception as e:
            print(f"错误: {e}")

if __name__ == "__main__":
    find_target_row()