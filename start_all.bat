@echo off

:: 启动后端服务
echo 启动后端服务...
start "Backend Server" cmd /c "cd d:\Git_Repository\Mathemist\backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload"

:: 等待后端服务启动
echo 等待后端服务启动...
ping 127.0.0.1 -n 10 > nul

:: 启动前端服务
echo 启动前端服务...
start "Frontend Server" cmd /c "cd d:\Git_Repository\Mathemist\frontend && pnpm dev --port 3003"

:: 等待前端服务启动
echo 等待前端服务启动...
ping 127.0.0.1 -n 15 > nul

:: 打开前端界面
echo 打开前端界面...
start http://localhost:3003

echo 服务启动完成！
echo 后端服务: http://localhost:8000
echo 前端服务: http://localhost:3003

echo 按任意键退出...
pause > nul