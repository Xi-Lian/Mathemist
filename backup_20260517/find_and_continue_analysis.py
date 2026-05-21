import pandas as pd
import os

def find_exercise_position():
    """找到指定习题在表格中的位置"""
    files = [
        r'd:\Git_Repository\Mathemist\learning_resource\函数习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\概率与统计习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\立体几何习题_云端资源汇总表.xlsx'
    ]
    
    target_title = '5-1-2弧度制'
    
    for file_path in files:
        if os.path.exists(file_path):
            try:
                df = pd.read_excel(file_path)
                for idx, row in df.iterrows():
                    if 'title' in df.columns and str(row['title']).strip() == target_title:
                        print(f"找到习题位置:")
                        print(f"  文件: {os.path.basename(file_path)}")
                        print(f"  行号: {idx + 1}")
                        print(f"  title: {row['title']}")
                        print(f"  该文件总行数: {len(df)}")
                        print(f"  后续还有 {len(df) - idx - 1} 道题")
                        return file_path, idx
            except Exception as e:
                print(f"读取 {file_path} 失败: {e}")
    
    print("未找到该习题")
    return None, -1

if __name__ == "__main__":
    file_path, idx = find_exercise_position()
    print(f"\n文件位置: {file_path}")
    print(f"起始行号: {idx + 1}")
