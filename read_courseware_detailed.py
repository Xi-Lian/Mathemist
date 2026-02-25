import pandas as pd

courseware_path = r'd:\Git_Repository\Mathemist\learning_resource\课件\课件汇总（必修一2.3-5.7）.xlsx'
df = pd.read_excel(courseware_path, header=None)

print("课件汇总表完整内容（前10行）：")
print("=" * 120)
for i in range(min(10, len(df))):
    print(f"第{i}行: {df.iloc[i].tolist()}")

# 尝试读取第0行作为表头
print("\n" + "=" * 120)
print("尝试将第0行作为表头：")
df_with_header = pd.read_excel(courseware_path, header=0)
print(f"字段列表: {df_with_header.columns.tolist()}")
print("\n前5行数据:")
print(df_with_header.head(5))
