"""
检查数据库中"简单随机抽样"相关的课例视频
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.core.vector_database_builder import VectorDatabaseBuilder

vdb = VectorDatabaseBuilder('learning_resource')
client = vdb.get_chroma_client()

# 检查所有集合
collections = client.list_collections()
print("=" * 80)
print("检查所有集合中的课例视频")
print("=" * 80)

for col in collections:
    print(f"\n集合: {col.name}")
    
    # 获取所有课例视频资源
    try:
        results = col.get(
            where={'resource_type': 'lesson_case'},
            include=['metadatas'],
            limit=100
        )
        
        if results['metadatas']:
            print(f"  找到 {len(results['metadatas'])} 个课例视频")
            
            # 查找包含"简单随机抽样"或"抽样"的资源
            matching_resources = []
            for metadata in results['metadatas']:
                filename = metadata.get('文件名', '')
                title = metadata.get('title', '')
                analysis = metadata.get('分析', '')
                
                if '简单随机抽样' in filename or '简单随机抽样' in title or '简单随机抽样' in analysis or \
                   '抽样' in filename or '抽样' in title or '抽样' in analysis:
                    matching_resources.append({
                        '文件名': filename[:60],
                        '标题': title[:60],
                        '分析': analysis[:100] if analysis else '',
                    })
            
            if matching_resources:
                print(f"  其中 {len(matching_resources)} 个与'抽样'相关:")
                for i, res in enumerate(matching_resources[:5], 1):
                    print(f"    {i}. 文件名: {res['文件名']}")
                    print(f"       标题: {res['标题']}")
                    print(f"       分析: {res['分析']}...")
                    print()
            else:
                print(f"  未找到与'抽样'相关的课例视频")
                
                # 显示前3个课例视频作为参考
                print(f"  前3个课例视频示例:")
                for i, metadata in enumerate(results['metadatas'][:3], 1):
                    print(f"    {i}. 文件名: {metadata.get('文件名', '')[:60]}")
                    print(f"       标题: {metadata.get('title', '')[:60]}")
                    print()
        else:
            print(f"  没有课例视频资源")
            
    except Exception as e:
        print(f"  查询失败: {e}")
