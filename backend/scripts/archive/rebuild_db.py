"""
重建向量数据库脚本
"""

import sys
import os

# 设置环境变量以避免编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'

from app.core.vector_database_builder import VectorDatabaseBuilder

if __name__ == "__main__":
    # 构建数据库
    builder = VectorDatabaseBuilder("d:\Git_Repository\Mathemist\learning_resource")
    
    # 强制重建数据库
    success = builder.build_vector_database(force_rebuild=True, batch_size=50)
    
    if success:
        print("向量数据库重建成功！")
    else:
        print("向量数据库重建失败！")
        sys.exit(1)
