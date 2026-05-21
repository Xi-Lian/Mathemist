import pandas as pd
import os

def find_md_position():
    """找到指定MD文件在表格中的位置"""
    files = [
        ('函数习题_云端资源汇总表.xlsx', '函数'),
        ('概率与统计习题_云端资源汇总表.xlsx', '概率与统计'),
        ('立体几何习题_云端资源汇总表.xlsx', '立体几何')
    ]
    
    target_md = '5-1-2弧度制.md'
    
    for file_name, category in files:
        file_path = rf'd:\Git_Repository\Mathemist\learning_resource\{file_name}'
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                for idx, row in df.iterrows():
                    if str(row['文件名']).strip() == target_md:
                        print(f"找到MD文件位置:")
                        print(f"  表格文件: {file_name}")
                        print(f"  在表格中的行号: {idx + 1}")
                        print(f"  文件名: {row['文件名']}")
                        print(f"  该表格共有 {len(df)} 个MD文件")
                        print(f"  该表格后续还有 {len(df) - idx - 1} 个MD文件")
                        print(f"\n表格内容分布:")
                        print(f"  函数习题: 208个MD文件")
                        print(f"  概率与统计: 33个MD文件")
                        print(f"  立体几何: 172个MD文件")
                        print(f"  总计: {208 + 33 + 172}个MD文件")
                        return file_name, idx
            except Exception as e:
                print(f"读取 {file_name} 失败: {e}")
    
    print("未找到该MD文件")
    return None, -1

if __name__ == "__main__":
    find_md_position()
