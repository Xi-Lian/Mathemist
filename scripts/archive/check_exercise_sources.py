#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pandas as pd

def check_exercise_files():
    print("=" * 80)
    print("Exercise Source File Validation")
    print("=" * 80)
    
    source_files = [
        '概率与统计习题_云端资源汇总表.xlsx',
        '函数习题_云端资源汇总表.xlsx', 
        '立体几何习题_云端资源汇总表.xlsx'
    ]
    
    full_source_paths = [
        r'd:\Git_Repository\Mathemist\learning_resource\概率与统计习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\函数习题_云端资源汇总表.xlsx',
        r'd:\Git_Repository\Mathemist\learning_resource\立体几何习题_云端资源汇总表.xlsx'
    ]
    
    analysis_dir = r'd:\Git_Repository\Mathemist\learning_resource\exercise_analysis'
    
    # 获取所有已分析的习题及其来源
    analyzed_by_source = {}
    for f in os.listdir(analysis_dir):
        if f.endswith('.json'):
            file_path = os.path.join(analysis_dir, f)
            try:
                with open(file_path, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    if data.get('analysis') and len(data['analysis']) > 0:
                        source = data.get('source_file', '')
                        if source not in analyzed_by_source:
                            analyzed_by_source[source] = []
                        analyzed_by_source[source].append(data['exercise_id'])
            except:
                pass
    
    print("Total analyzed exercises: %d" % sum(len(v) for v in analyzed_by_source.values()))
    print("Unique source files: %d" % len(analyzed_by_source.keys()))
    print()
    
    total_exercises = 0
    total_found = 0
    
    for idx, source_file in enumerate(source_files):
        print("-" * 80)
        print("Source file: %s" % source_file)
        
        full_path = full_source_paths[idx]
        
        if not os.path.exists(full_path):
            print("File not found!")
            print()
            continue
        
        try:
            df = pd.read_excel(full_path)
            print("Total rows in Excel: %d" % len(df))
            
            # 计算分析中来自此文件的数量
            found_count = 0
            for source in analyzed_by_source.keys():
                if source_file in source or source_file.replace('.xlsx', '') in source:
                    found_count += len(analyzed_by_source[source])
            
            print("Found in analysis: %d" % found_count)
            print("Coverage: %.1f%%" % (found_count / len(df) * 100))
            
            total_exercises += len(df)
            total_found += found_count
            
        except Exception as e:
            print("Error parsing file: %s" % str(e))
        
        print()
    
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print("Total rows in source files: %d" % total_exercises)
    print("Successfully analyzed: %d" % total_found)
    print("Overall coverage: %.1f%%" % (total_found / total_exercises * 100))

if __name__ == "__main__":
    check_exercise_files()
