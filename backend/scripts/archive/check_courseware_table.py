import pandas as pd
import os

# 检查课件汇总表
courseware_file = r'd:\Git_Repository\Mathemist\learning_resource\概率与统计-课件汇总.xlsx'

if not os.path.exists(courseware_file):
    print(f"文件不存在: {courseware_file}")
else:
    print(f"文件存在: {courseware_file}")
    
    try:
        df = pd.read_excel(courseware_file)
        print(f"\n课件汇总表内容:")
        print(f"行数: {len(df)}")
        print(f"列名: {list(df.columns)}")
        
        # 检查是否有"组合数"相关的课件
        combination_courseware = df[df.apply(lambda row: any('组合数' in str(v) for v in row.values), axis=1)]
        print(f"\n组合数相关课件数量: {len(combination_courseware)}")
        
        if len(combination_courseware) > 0:
            print("\n组合数相关课件详情:")
            for i, row in combination_courseware.iterrows():
                print(f"\n  课件{i+1}:")
                for col in df.columns:
                    val = str(row[col]) if pd.notna(row[col]) else ''
                    # 处理编码问题
                    val = val.encode('gbk', errors='ignore').decode('gbk')
                    print(f"    {col}: {val}")
        
        # 检查教学用途字段
        if '教学用途' in df.columns:
            print(f"\n教学用途字段统计:")
            # 统计教学用途的分布
            usage_counts = df['教学用途'].value_counts().to_dict()
            for usage, count in usage_counts.items():
                usage_str = str(usage).encode('gbk', errors='ignore').decode('gbk')
                print(f"  {usage_str}: {count}条")
            
            # 检查练习课课件
            exercise_courseware = df[df['教学用途'].str.contains('练习课', na=False)]
            print(f"\n练习课课件数量: {len(exercise_courseware)}")
            
    except Exception as e:
        print(f"读取文件失败: {e}")
        import traceback
        traceback.print_exc()
