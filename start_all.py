#!/usr/bin/env python3
"""
启动前后端服务的脚本
"""

import subprocess
import os
import time
import webbrowser

# 后端服务配置
backend_dir = "d:\Git_Repository\Mathemist\backend"
backend_cmd = ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# 前端服务配置
frontend_dir = "d:\Git_Repository\Mathemist\frontend"
frontend_cmd = ["pnpm", "dev", "--port", "3003"]

# 启动后端服务
print("启动后端服务...")
backend_process = subprocess.Popen(backend_cmd, cwd=backend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# 等待后端服务启动
print("等待后端服务启动...")
time.sleep(5)

# 启动前端服务
print("启动前端服务...")
frontend_process = subprocess.Popen(frontend_cmd, cwd=frontend_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

# 等待前端服务启动
print("等待前端服务启动...")
time.sleep(10)

# 打开前端界面
print("打开前端界面...")
webbrowser.open("http://localhost:3003")

# 显示服务状态
print("\n服务启动完成！")
print("后端服务: http://localhost:8000")
print("前端服务: http://localhost:3003")
print("\n按Ctrl+C停止服务...")

# 等待用户输入
try:
    input()
except KeyboardInterrupt:
    pass

# 停止服务
print("\n停止服务...")
backend_process.terminate()
frontend_process.terminate()
print("服务已停止。")