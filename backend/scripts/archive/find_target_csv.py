import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import glob
import csv

def find_index_with_target():
    """
    找到包含目标教案的索引文件
    """
    search_dir = r"D:\Git_Repository\Mathemist\learning_resource"

    for root, dirs, files in os.walk(search_dir):
        for file in files:
            if file.endswith('.csv') or file.endswith('.md'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        if '3310' in content:
                            print(f"找到: {filepath}")

                            # 如果是CSV，检查具体行
                            if file.endswith('.csv'):
                                try:
                                    reader = csv.DictReader(content.splitlines())
                                    for row in reader:
                                        filename = str(row.get('文件名', ''))
                                        if '3310' in filename:
                                            print(f"  文件名: {filename}")
                                            print(f"  云端链接: {row.get('云端链接', '')}")
                                            print(f"  扩展名: {row.get('扩展名', '')}")
                                except Exception as e:
                                    print(f"  CSV解析错误: {e}")
                except Exception as e:
                    pass

if __name__ == "__main__":
    find_index_with_target()