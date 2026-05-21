import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import os
import glob
import csv

def find_target_in_cloud_index():
    """
    在云端教案索引中查找目标教案
    """
    # 搜索索引文件
    search_patterns = [
        r"D:\Git_Repository\Mathemist\**\*云端*教案*索引*.csv",
        r"D:\Git_Repository\Mathemist\**\*lesson*plan*index*.csv",
        r"D:\Git_Repository\Mathemist\**\*教案*.csv",
    ]

    index_files = []
    for pattern in search_patterns:
        index_files.extend(glob.glob(pattern, recursive=True))

    # 也尝试MD文件
    md_patterns = [
        r"D:\Git_Repository\Mathemist\**\*云端*教案*索引*.md",
    ]
    for pattern in md_patterns:
        index_files.extend(glob.glob(pattern, recursive=True))

    print(f"找到的索引文件: {index_files}")

    # 搜索learning-resource相关的文件夹
    lr_patterns = [
        r"D:\Git_Repository\Mathemist\**\*learning-resource*",
        r"D:\Git_Repository\Mathemist\**\*learning_resource*",
    ]

    for pattern in lr_patterns:
        results = glob.glob(pattern, recursive=True)
        if results:
            print(f"\n找到learning相关: {results[:10]}")

    # 搜索任何包含"教案"关键词的CSV
    csv_files = glob.glob(r"D:\Git_Repository\Mathemist\**\*.csv", recursive=True)
    lesson_plan_csvs = [f for f in csv_files if '教案' in f or 'lesson' in f.lower()]
    print(f"\n包含教案的CSV文件: {lesson_plan_csvs[:10]}")

    # 直接搜索3310
    print("\n搜索包含'3310'的文件...")
    for csv_file in csv_files[:50]:
        try:
            with open(csv_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '3310' in content:
                    print(f"找到: {csv_file}")

                    # 读取CSV查找3310行
                    try:
                        reader = csv.DictReader(content.splitlines())
                        for row in reader:
                            filename = str(row.get('文件名', '')) + str(row.get('文件名', ''))
                            if '3310' in filename:
                                print(f"  行内容: 文件名={row.get('文件名', '')}, 云端链接={row.get('云端链接', '')}, 扩展名={row.get('扩展名', '')}")
                    except:
                        pass
        except Exception as e:
            pass

if __name__ == "__main__":
    find_target_in_cloud_index()