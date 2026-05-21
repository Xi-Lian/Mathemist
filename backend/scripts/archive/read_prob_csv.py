import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import csv

def find_target():
    """
    查找目标教案
    """
    csv_file = r"D:\Git_Repository\Mathemist\learning_resource\概率与统计-教案资源信息汇总表.csv"

    # 尝试不同编码
    for encoding in ['utf-8', 'gbk', 'gb2312', 'latin1']:
        try:
            print(f"尝试编码: {encoding}")
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                print(f"列名: {headers[:10] if headers else 'None'}...")

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
            print("未找到目标教案")
            return
        except Exception as e:
            print(f"  失败: {e}")

if __name__ == "__main__":
    find_target()