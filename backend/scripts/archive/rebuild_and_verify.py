#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def rebuild_and_verify():
    """重新构建向量数据库并验证课件资源分类"""
    print("重新构建向量数据库并验证课件资源分类")
    print("="*60)
    
    from app.core.vector_database_builder import VectorDatabaseBuilder
    import chromadb
    
    # 构建向量数据库
    print("\n1. 重新构建向量数据库...")
    builder = VectorDatabaseBuilder("D:/Git_Repository/Mathemist/learning_resource")
    success = builder.build_vector_database(force_rebuild=True, batch_size=50)
    
    if not success:
        print("❌ 向量数据库构建失败")
        return False
    
    # 验证结果
    print("\n2. 验证课件资源分类...")
    client = chromadb.PersistentClient(path="D:/Git_Repository/Mathemist/backend/chroma_db")
    
    expected_counts = {
        "math_resources_function": 361,    # 函数-课件汇总.xlsx
        "math_resources_geometry": 354,    # 立体几何-课件汇总.xlsx
        "math_resources_probability": 372, # 概率与统计-课件汇总.xlsx
        "math_resources_algebra": 354,     # 代数-课件汇总.xlsx
    }
    
    all_correct = True
    for coll_name, expected in expected_counts.items():
        try:
            coll = client.get_collection(coll_name)
            count = coll.count()
            
            # 获取课件资源数量
            results = coll.get()
            metadatas = results.get('metadatas', [])
            courseware_count = sum(1 for meta in metadatas if meta.get("resource_type") == 'courseware')
            
            print(f"   {coll_name}: {courseware_count} 条课件 (预期: {expected})")
            
            if courseware_count == expected:
                print(f"      ✅ 分类正确")
            else:
                print(f"      ❌ 分类错误，缺少 {expected - courseware_count} 条")
                all_correct = False
                
        except Exception as e:
            print(f"   {coll_name}: 错误 - {e}")
            all_correct = False
    
    if all_correct:
        print("\n✅ 所有课件资源分类正确！")
    else:
        print("\n❌ 课件资源分类存在问题")
    
    return all_correct

if __name__ == "__main__":
    try:
        success = rebuild_and_verify()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
