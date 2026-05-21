import pandas as pd
import os

def check_structure():
    files = [
        r'd:\Git_Repository\Mathemist\learning_resource\函数习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\概率与统计习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\立体几何习题_云端资源汇总表.xlsx'
    ]
    
    for file_path in files:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                print(f"文件: {os.path.basename(file_path)}")
                print(f"  行数: {len(df)}")
                print(f"  列名: {list(df.columns)}")
                if len(df) > 0:
                    print(f"  第一行数据:")
                    for col in df.columns[:5]:  # 只显示前5列
                        print(f"    {col}: {str(df.iloc[0][col])[:50]}")
                print()
            except Exception as e:
                print(f"读取 {file_path} 失败: {e}\n")

if __name__ == "__main__":
    check_structure()
