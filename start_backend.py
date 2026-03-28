#!/usr/bin/env python3
"""
启动后端服务的脚本
"""

import subprocess
import os

# 切换到后端目录
backend_dir = "d:\Git_Repository\Mathemist\backend"
os.chdir(backend_dir)

# 启动uvicorn服务器
cmd = ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

print(f"启动后端服务: {' '.join(cmd)}")
print(f"工作目录: {os.getcwd()}")

# 执行命令
process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# 实时输出日志
for line in process.stdout:
    print(line.strip())

# 等待进程结束
process.wait()