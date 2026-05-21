#!/bin/bash
# ============================================
# Mathemist 生产环境部署脚本
# 适用于 Ubuntu/CentOS 服务器
# ============================================

set -e  # 遇到错误立即退出

echo "🚀 开始部署 Mathemist 系统..."

# ============================================
# 1. 系统更新和基础依赖安装
# ============================================
echo ""
echo "📦 步骤 1/8: 安装系统依赖..."

# Ubuntu/Debian
if [ -f /etc/debian_version ]; then
    sudo apt-get update
    sudo apt-get install -y \
        python3-pip \
        python3-venv \
        nginx \
        certbot \
        python3-certbot-nginx \
        git \
        curl \
        wget
# CentOS/RHEL
elif [ -f /etc/redhat-release ]; then
    sudo yum update -y
    sudo yum install -y \
        python3-pip \
        python3-devel \
        nginx \
        epel-release \
        git \
        curl \
        wget
fi

echo "✅ 系统依赖安装完成"

# ============================================
# 2. 创建项目目录
# ============================================
echo ""
echo "📁 步骤 2/8: 创建项目目录..."

PROJECT_DIR="/opt/mathemist"
sudo mkdir -p $PROJECT_DIR
sudo chown -R $USER:$USER $PROJECT_DIR

echo "✅ 项目目录创建完成: $PROJECT_DIR"

# ============================================
# 3. 上传项目代码
# ============================================
echo ""
echo "📤 步骤 3/8: 请上传项目代码到 $PROJECT_DIR"
echo ""
echo "在你的本地机器执行："
echo "  scp -r backend/ root@49.233.140.116:$PROJECT_DIR/"
echo "  scp -r frontend/ root@49.233.140.116:$PROJECT_DIR/"
echo "  scp learning_resource/ root@49.233.140.116:$PROJECT_DIR/"
echo ""
read -p "按回车键继续（确保代码已上传）..."

# ============================================
# 4. 配置 Python 虚拟环境
# ============================================
echo ""
echo "🐍 步骤 4/8: 配置 Python 环境..."

cd $PROJECT_DIR/backend

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

echo "✅ Python 环境配置完成"

# ============================================
# 5. 配置环境变量
# ============================================
echo ""
echo "⚙️  步骤 5/8: 配置环境变量..."

cat > .env << EOF
# DeepSeek API 配置（如果使用云端 API）
DEEPSEEK_API_KEY=your-api-key-here
DEEPSEEK_MODEL=deepseek-chat

# 如果使用本地部署的大模型，注释上面的，使用下面的
# LLM_PROVIDER=local
# LOCAL_MODEL_PATH=/opt/models/deepseek-r1

# 服务器配置
HOST=0.0.0.0
PORT=8000

# CORS 配置（生产环境应该指定具体域名）
CORS_ORIGINS=http://49.233.140.116,https://your-domain.com

# ChromaDB 路径
CHROMA_DB_PATH=$PROJECT_DIR/backend/chroma_db

# 日志级别
LOG_LEVEL=INFO
EOF

echo "✅ 环境变量配置完成"
echo "⚠️  请编辑 .env 文件，填入正确的 API Key 或配置本地模型"

# ============================================
# 6. 安装 Node.js 和前端依赖
# ============================================
echo ""
echo "📦 步骤 6/8: 安装前端依赖..."

# 安装 Node.js 18 LTS
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 pnpm
npm install -g pnpm

# 安装前端依赖
cd $PROJECT_DIR/frontend
pnpm install

# 构建前端
pnpm build

echo "✅ 前端构建完成"

# ============================================
# 7. 配置 Nginx
# ============================================
echo ""
echo "🌐 步骤 7/8: 配置 Nginx..."

sudo tee /etc/nginx/sites-available/mathemist << 'EOF'
server {
    listen 80;
    server_name 49.233.140.116 your-domain.com;

    # 前端静态文件
    location / {
        root /opt/mathemist/frontend/out;
        try_files $uri $uri/ /index.html;
        expires 1d;
        add_header Cache-Control "public, immutable";
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置（大模型推理可能需要较长时间）
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # LangGraph API 代理
    location /langgraph/ {
        proxy_pass http://127.0.0.1:8000/langgraph/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # 超时设置
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # GGB API 代理
    location /ggb/ {
        proxy_pass http://127.0.0.1:8000/ggb/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
    }
}
EOF

# 启用站点
sudo ln -sf /etc/nginx/sites-available/mathemist /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

echo "✅ Nginx 配置完成"

# ============================================
# 8. 配置 systemd 服务
# ============================================
echo ""
echo "🔧 步骤 8/8: 配置系统服务..."

# 后端服务
sudo tee /etc/systemd/system/mathemist-backend.service << EOF
[Unit]
Description=Mathemist Backend Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/backend
Environment="PATH=$PROJECT_DIR/backend/venv/bin"
ExecStart=$PROJECT_DIR/backend/venv/bin/python main.py
Restart=always
RestartSec=10

# 资源限制
LimitNOFILE=65536

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=mathemist-backend

[Install]
WantedBy=multi-user.target
EOF

# 重新加载 systemd
sudo systemctl daemon-reload

# 启用并启动服务
sudo systemctl enable mathemist-backend
sudo systemctl start mathemist-backend

echo "✅ 系统服务配置完成"

# ============================================
# 完成
# ============================================
echo ""
echo "=========================================="
echo "🎉 部署完成！"
echo "=========================================="
echo ""
echo "📊 服务状态检查："
echo "  后端服务: sudo systemctl status mathemist-backend"
echo "  Nginx:    sudo systemctl status nginx"
echo ""
echo "📝 日志查看："
echo "  后端日志: sudo journalctl -u mathemist-backend -f"
echo "  Nginx日志: sudo tail -f /var/log/nginx/error.log"
echo ""
echo "🌐 访问地址："
echo "  HTTP:  http://49.233.140.116"
echo ""
echo "🔒 启用 HTTPS（可选）："
echo "  sudo certbot --nginx -d your-domain.com"
echo ""
echo "⚠️  重要提示："
echo "  1. 请编辑 backend/.env 文件，配置正确的 API Key"
echo "  2. 确保防火墙开放 80 和 443 端口"
echo "  3. 建议配置域名并启用 HTTPS"
echo ""
