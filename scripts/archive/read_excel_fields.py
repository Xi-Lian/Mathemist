import pandas as pd
import os

print("=" * 80)
print("学习资源汇总表字段分析")
print("=" * 80)

# 1. 课件汇总表
print("\n【1. 课件汇总表】")
courseware_path = r'd:\Git_Repository\Mathemist\learning_resource\课件\课件汇总（必修一2.3-5.7）.xlsx'
if os.path.exists(courseware_path):
    df_courseware = pd.read_excel(courseware_path)
    print(f"字段列表: {df_courseware.columns.tolist()}")
    print("\n前3行数据:")
    print(df_courseware.head(3))
else:
    print("文件不存在")

# 2. GGB汇总表
print("\n" + "=" * 80)
print("【2. GGB汇总表】")
ggb_path = r'd:\Git_Repository\Mathemist\learning_resource\ggb\ggb信息.xlsx'
if os.path.exists(ggb_path):
    df_ggb = pd.read_excel(ggb_path)
    print(f"字段列表: {df_ggb.columns.tolist()}")
    print("\n前3行数据:")
    print(df_ggb.head(3))
else:
    print("文件不存在")

# 3. 查看一个具体的习题文件
print("\n" + "=" * 80)
print("【3. 习题文件示例】")
exercise_sample = r'd:\Git_Repository\Mathemist\learning_resource\习题\必修一第三章-函数的概念\3-1-1函数的概念.md'
if os.path.exists(exercise_sample):
    with open(exercise_sample, 'r', encoding='utf-8') as f:
        content = f.read()
        print(content[:500])
else:
    print("示例文件不存在")
