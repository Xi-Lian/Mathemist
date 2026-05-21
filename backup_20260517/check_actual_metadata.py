
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

import chromadb

# 设置数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'backend', 'chroma_db')
print(f"数据库路径: {db_path}")

client = chromadb.PersistentClient(path=db_path)
collection = client.get_collection('math_resources_probability')

# 获取所有课件
results = collection.get(
    where={"resource_type": "courseware"},
    include=["documents", "metadatas"]
)

print(f"\n总课件数: {len(results['documents'])}")

# 查找包含"分类加法计数原理"的课件
print(f"\n查找包含'分类加法计数原理'的课件:")
found = False
for i, (doc, meta) in enumerate(zip(results['documents'], results['metadatas'])):
    if '分类加法计数原理' in doc:
        print(f"\n  课件 {i+1}:")
        print(f"    标题: {meta.get('title', 'N/A')}")
        print(f"    文件名: {meta.get('filename', 'N/A')}")
        print(f"    教学用途: {meta.get('教学用途', 'N/A')}")
        print(f"    资源类型: {meta.get('resource_type', 'N/A')}")
        print(f"    文档片段: {doc[:100]}...")
        found = True
        
        # 检查是否是练习课课件
        if '练习课' in str(meta.get('教学用途', '')):
            print(f"    ✓ 这是练习课课件！")

if not found:
    print("  未找到相关课件")
