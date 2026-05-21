#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_all_courseware():
    """验证所有板块的课件资源是否被成功处理"""
    print("验证所有板块的课件资源处理情况")
    print("="*60)
    
    from app.core.resource_table.service import ResourceTableParser
    import chromadb
    
    # 解析所有课件资源
    parser = ResourceTableParser("D:/Git_Repository/Mathemist/learning_resource")
    courseware_list = parser.parse_courseware_table()
    
    print("1. 原始课件资源统计:")
    file_groups = {}
    for courseware in courseware_list:
        source_file = courseware.get('source_file', '未知')
        if source_file not in file_groups:
            file_groups[source_file] = []
        file_groups[source_file].append(courseware)
    
    for filename, coursewares in file_groups.items():
        print(f"   {filename}: {len(coursewares)} 条")
    
    # 检查向量数据库中的课件资源
    print("\n2. 向量数据库中课件资源统计:")
    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    
    collections = client.list_collections()
    total_db_courseware = 0
    
    for coll in collections:
        count = coll.count()
        if count > 0:
            results = coll.get()
            metadatas = results.get('metadatas', [])
            
            courseware_count = 0
            for meta in metadatas:
                if meta.get("resource_type") == 'courseware':
                    courseware_count += 1
            
            total_db_courseware += courseware_count
            print(f"   {coll.name}: {courseware_count} 条课件")
    
    print(f"\n   总计: {total_db_courseware} 条课件")
    
    # 对比
    total_original = sum(len(coursewares) for coursewares in file_groups.values())
    print(f"\n3. 对比结果:")
    print(f"   原始汇总表课件数: {total_original}")
    print(f"   向量数据库课件数: {total_db_courseware}")
    
    if total_original == total_db_courseware:
        print("   ✅ 所有课件资源都已成功处理")
        return True
    else:
        print(f"   ❌ 课件资源处理不完整，缺少 {total_original - total_db_courseware} 条")
        return False

if __name__ == "__main__":
    try:
        verify_all_courseware()
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
