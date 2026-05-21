"""
列出所有教案
"""

import sys
sys.path.insert(0, 'd:\\Git_Repository\\Mathemist\\backend')

from app.core.resource_table_parser import ResourceTableParser

parser = ResourceTableParser('d:\\Git_Repository\\Mathemist\\learning_resource')

# 获取所有资源
all_tables = parser.parse_all_tables()
lesson_plans = all_tables.get('lesson_plans', [])

print(f"共找到 {len(lesson_plans)} 个教案\n")

for i, resource in enumerate(lesson_plans[:20]):
    title = resource.get('title', '')
    file_topic = resource.get('文件名主题', '')
    print(f"{i+1}. {title}")
    print(f"   文件名主题: {file_topic}")
    print()
