#!/usr/bin/env python
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def rebuild_vector_db():
    """重新构建向量数据库，包含课件资源"""
    print("重新构建向量数据库")
    print("="*60)
    
    from app.core.vector_database_builder import VectorDatabaseBuilder
    
    builder = VectorDatabaseBuilder("D:/Git_Repository/Mathemist/learning_resource")
    
    print("\n开始构建向量数据库...")
    success = builder.build_vector_database(force_rebuild=True, batch_size=50)
    
    if success:
        print("\n✅ 向量数据库构建成功！")
    else:
        print("\n❌ 向量数据库构建失败")
    
    return success

if __name__ == "__main__":
    try:
        success = rebuild_vector_db()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
