import sys
import os
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.resource_table_parser import ResourceTableParser
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# 初始化解析器
lr_path = Path("d:/Git_Repository/Mathemist/learning_resource")
parser = ResourceTableParser(str(lr_path))

# 解析所有资源
all_resources = parser.parse_all_tables()

print("=" * 80)
print("解析的资源统计:")
print("=" * 80)

for resource_type, resources in all_resources.items():
    print(f"\n{resource_type}: {len(resources)}条记录")
    
    if resources:
        print(f"  示例资源:")
        sample = resources[0]
        print(f"    - resource_type: {sample.get('resource_type', 'NOT SET')}")
        print(f"    - source_file: {sample.get('source_file', 'NOT SET')}")
        print(f"    - title: {sample.get('title', 'NOT SET')}")
        
        # 对于课例，显示更多信息
        if resource_type == 'lesson_case':
            print(f"    - 章节: {sample.get('章节', 'NOT SET')}")
            print(f"    - 视频文件名/网址: {sample.get('视频文件名/网址', 'NOT SET')}")
            print(f"    - 分析: {sample.get('分析', 'NOT SET')}")
