import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import csv

def find_associated_markdown():
    """
    查找与目标教案关联的Markdown文件
    """
    csv_file = r"D:\Git_Repository\Mathemist\learning_resource\概率与统计-教案资源信息汇总表.csv"

    with open(csv_file, 'r', encoding='gbk') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get('文件名', '')
            ext = row.get('扩展名', '')
            if ext == '.md' and '3310' in filename:
                print(f"Markdown文件: {filename}")
                print(f"关联文件: {row.get('关联文件', '')}")
                print(f"云端链接: {row.get('云端链接', '')}")
                return

    print("未找到关联的Markdown文件")

if __name__ == "__main__":
    find_associated_markdown()