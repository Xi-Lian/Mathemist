import pandas as pd

# 读取课件汇总表
df = pd.read_excel('learning_resource/概率与统计-课件汇总.xlsx')

print('=== 概率与统计课件汇总表结构 ===')
print(f'总行数: {len(df)}')
print(f'列名: {df.columns.tolist()}')
print()

# 查找教学用途为练习课课件的记录
if '教学用途' in df.columns:
    practice_courseware = df[df['教学用途'].astype(str).str.contains('练习课课件', na=False)]
    print('=== 练习课课件统计 ===')
    print(f'总练习课课件数: {len(practice_courseware)}')
    print()
    
    # 查找包含'分类加法计数原理'的记录
    if '内容' in df.columns:
        classification_courseware = practice_courseware[practice_courseware['内容'].astype(str).str.contains('分类加法计数原理', na=False)]
        print('=== 分类加法计数原理相关的练习课课件 ===')
        print(f'数量: {len(classification_courseware)}')
        print()
        if len(classification_courseware) > 0:
            for idx, row in classification_courseware.iterrows():
                print(f'内容: {row.get("内容", "")}')
                print(f'文件名: {row.get("文件名", "")}')
                print(f'教学用途: {row.get("教学用途", "")}')
                print()
    else:
        print('没有找到"内容"列')
else:
    print('没有找到"教学用途"列')
