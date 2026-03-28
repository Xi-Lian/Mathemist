#!/usr/bin/env python3
"""
直接运行后端服务的脚本
"""

import os
import sys

# 切换到后端目录
backend_dir = "d:\Git_Repository\Mathemist\backend"
os.chdir(backend_dir)

# 添加当前目录到Python路径
sys.path.insert(0, os.getcwd())

# 导入并运行应用
from main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)