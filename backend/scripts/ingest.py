import os
import traceback
from pathlib import Path
import sys

# 添加backend目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.vector_database_builder import VectorDatabaseBuilder

def main():
    SCRIPT_DIR = Path(__file__).parent.parent.parent
    DOCS_DIR = SCRIPT_DIR / "learning_resource"
    
    try:
        if not os.path.exists(DOCS_DIR):
            raise FileNotFoundError(f"文档目录不存在：{DOCS_DIR}")
        
        print(f"📂 使用向量数据库构建器构建向量数据库...")
        print(f"📂 文档目录：{DOCS_DIR}")
        
        # 创建向量数据库构建器
        builder = VectorDatabaseBuilder(str(DOCS_DIR))
        
        # 构建向量数据库
        success = builder.build_vector_database(force_rebuild=True)
        
        if success:
            print(f"🎉 向量数据库构建完成！")
        else:
            raise ValueError("向量数据库构建失败")
        
    except Exception as e:
        print(f"\n❌ 执行失败：{str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
