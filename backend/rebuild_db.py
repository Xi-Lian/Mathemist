import os
import sys
from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    # 设置学习资源路径
    learning_resource_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'learning_resource')
    
    print(f"开始构建向量数据库，学习资源路径: {learning_resource_path}")
    
    # 初始化构建器
    builder = VectorDatabaseBuilder(learning_resource_path=learning_resource_path)
    
    # 构建数据库
    builder.build_vector_database(force_rebuild=True)
    
    print("向量数据库构建完成！")

if __name__ == "__main__":
    main()