#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json

def validate_exercise_analysis():
    print("=" * 80)
    print("Exercise Analysis Validation Report")
    print("=" * 80)
    
    analysis_dir = os.path.join(os.path.dirname(__file__), 'learning_resource', 'exercise_analysis')
    
    analysis_files = []
    for f in os.listdir(analysis_dir):
        if f.endswith('.json'):
            analysis_files.append(os.path.join(analysis_dir, f))
    
    print("Total analysis files found: %d" % len(analysis_files))
    
    validated_count = 0
    incomplete_count = 0
    issues = []
    
    print("\nValidating analysis files...")
    print("-" * 80)
    
    for file_path in analysis_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查必需字段
            required_fields = ['exercise_id', 'resource_type', 'title', 'source_file', 'analysis', 'original_resource']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                incomplete_count += 1
                issues.append("MISSING_FIELDS %s: %s" % (str(missing_fields), os.path.basename(file_path)))
                continue
            
            # 检查 analysis 字段不为空
            if not data['analysis'] or len(data['analysis']) == 0:
                incomplete_count += 1
                issues.append("EMPTY_ANALYSIS: %s" % os.path.basename(file_path))
                continue
            
            # 检查 original_resource 不为空
            if not data['original_resource']:
                incomplete_count += 1
                issues.append("EMPTY_ORIGINAL: %s" % os.path.basename(file_path))
                continue
            
            validated_count += 1
            
        except Exception as e:
            incomplete_count += 1
            issues.append("PARSE_ERROR: %s - %s" % (os.path.basename(file_path), str(e)[:50]))
            continue
    
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)
    print("Total analysis files: %d" % len(analysis_files))
    print("Validated (all fields present): %d" % validated_count)
    print("Incomplete or invalid: %d" % incomplete_count)
    
    if issues:
        print("\nIssues found (%d):" % len(issues))
        for issue in issues[:20]:
            print("  %s" % issue)
        if len(issues) > 20:
            print("  ... and %d more issues" % (len(issues) - 20))
    
    print("\n" + "=" * 80)
    if incomplete_count == 0:
        print("All analysis files are valid!")
    else:
        print("Some issues found. Please review the issues above.")

if __name__ == "__main__":
    validate_exercise_analysis()
