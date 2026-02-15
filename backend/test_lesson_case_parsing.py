import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.resource_table_parser import ResourceTableParser
from pathlib import Path

# 初始化解析器
lr_path = Path("d:/Git_Repository/Mathemist/learning_resource")
parser = ResourceTableParser(str(lr_path))

# 解析课例资源汇总表
lesson_cases = parser.parse_lesson_case_table()

print("=" * 80)
print(f"解析的课例资源数量: {len(lesson_cases)}")
print("=" * 80)

if lesson_cases:
    print("\n前5个课例资源:")
    for i in range(min(5, len(lesson_cases))):
        print(f"\n{i+1}. 资源:")
        print(f"   - resource_type: {lesson_cases[i].get('resource_type', 'NOT SET')}")
        print(f"   - source_file: {lesson_cases[i].get('source_file', 'NOT SET')}")
        print(f"   - 章节: {lesson_cases[i].get('章节', 'NOT SET')}")
        print(f"   - 教材: {lesson_cases[i].get('教材', 'NOT SET')}")
        print(f"   - 视频文件名/网址: {lesson_cases[i].get('视频文件名/网址', 'NOT SET')}")
        print(f"   - 分析: {lesson_cases[i].get('分析', 'NOT SET')}")
else:
    print("没有解析到课例资源")
