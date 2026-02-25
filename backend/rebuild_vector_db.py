#!/usr/bin/env python3
"""
重建向量数据库脚本
确保幂函数习题文件被正确索引
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.vector_database_builder import VectorDatabaseBuilder


def rebuild_vector_db():
    """
    重建向量数据库
    """
    print("\n" + "="*60)
    print("重建向量数据库")
    print("="*60)
    
    try:
        # 初始化向量数据库构建器
        builder = VectorDatabaseBuilder('d:\\Git_Repository\\Mathemist\\learning_resource')
        
        # 强制重建数据库
        print("开始重建向量数据库...")
        success = builder.build_vector_database(force_rebuild=True)
        
        if success:
            print("✅ 向量数据库重建成功！")
        else:
            print("❌ 向量数据库重建失败！")
            
    except Exception as e:
        print(f"❌ 重建失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    rebuild_vector_db()
