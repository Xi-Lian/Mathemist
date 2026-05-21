"""
检查向量数据库中课例视频的元数据字段
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()

print("=" * 80)
print("检查课例视频的元数据字段")
print("=" * 80)

# 检查math_resources_probability集合
collection = client.get_collection('math_resources_probability')

# 获取课例视频资源
results = collection.get(
    where={'resource_type': 'lesson_case'},
    include=['metadatas'],
    limit=5
)

if results['metadatas']:
    print(f"\n找到 {len(results['metadatas'])} 个课例视频\n")
    
    for i, metadata in enumerate(results['metadatas'][:3]):
        print(f"课例视频 {i+1}:")
        print(f"  所有字段: {list(metadata.keys())}")
        print()
        
        # 检查关键宇段
        key_fields = ['title', '课程名称', '教材', '章节', '分析', '视频文件名/网址', 'video_url', 'url']
        for field in key_fields:
            if field in metadata:
                value = metadata[field]
                if value:
                    value_str = str(value)[:100]
                    print(f"  {field}: {value_str}")
                else:
                    print(f"  {field}: (空)")
            else:
                print(f"  {field}: (不存在)")
        print()
else:
    print("\n没有找到课例视频资源")
