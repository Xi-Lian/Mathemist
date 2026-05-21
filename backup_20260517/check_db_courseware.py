import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.retrieval._shared import get_vector_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("=" * 100)
print("检查向量数据库中的课件资源")
print("=" * 100)
print()

# 检查各个板块的数据库
boards = ["函数", "几何", "概率统计", "代数"]

for board in boards:
    print(f"=== 检查板块: {board} ===")
    try:
        db = get_vector_db(board)
        collection = db._collection
        
        # 获取所有课件
        results = collection.get(
            where={"resource_type": "courseware"},
            include=["metadatas", "documents"]
        )
        
        print(f"课件总数: {len(results['ids'])}")
        
        # 查找包含"分类加法计数原理"的课件
        found = False
        for i, doc in enumerate(results['documents']):
            if "分类加法计数原理" in doc or "6.1" in doc:
                meta = results['metadatas'][i]
                print(f"✓ 找到相关课件:")
                print(f"  - 内容: {doc[:100]}...")
                print(f"  - 文件名: {meta.get('filename', 'N/A')}")
                print(f"  - 教学用途: {meta.get('teaching_use', 'N/A')}")
                print(f"  - ID: {results['ids'][i]}")
                found = True
        
        if not found and len(results['ids']) > 0:
            print("前5个课件:")
            for i in range(min(5, len(results['ids']))):
                meta = results['metadatas'][i]
                print(f"  {i+1}. {meta.get('filename', 'N/A')} - {meta.get('teaching_use', 'N/A')}")
        
        print()
    except Exception as e:
        print(f"✗ 出错: {e}")
        import traceback
        traceback.print_exc()
    print()
