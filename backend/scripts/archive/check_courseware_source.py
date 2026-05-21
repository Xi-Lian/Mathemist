#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def check_courseware_source():
    """检查课件资源的来源"""
    print("检查课件资源的来源")
    print("="*60)
    
    from app.core.resource_table.service import ResourceTableParser
    
    parser = ResourceTableParser("D:/Git_Repository/Mathemist/learning_resource")
    courseware_list = parser.parse_courseware_table()
    
    # 按source_file分组统计
    source_groups = {}
    for courseware in courseware_list:
        source_file = courseware.get('source_file', '未知')
        if source_file not in source_groups:
            source_groups[source_file] = []
        source_groups[source_file].append(courseware)
    
    print("课件资源来源统计:")
    for source_file, coursewares in source_groups.items():
        print(f"  {source_file}: {len(coursewares)} 条")
    
    # 检查是否有云端汇总表
    print("\n检查是否有云端汇总表...")
    cloud_sources = [k for k in source_groups.keys() if '云端' in k or 'cloud' in k.lower()]
    if cloud_sources:
        print(f"发现云端汇总表: {cloud_sources}")
        for src in cloud_sources:
            print(f"  {src}: {len(source_groups[src])} 条")
    
    # 检查本地汇总表
    print("\n本地汇总表:")
    local_sources = [k for k in source_groups.keys() if '云端' not in k and 'cloud' not in k.lower()]
    for src in local_sources:
        print(f"  {src}: {len(source_groups[src])} 条")
    
    return True

if __name__ == "__main__":
    try:
        check_courseware_source()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
