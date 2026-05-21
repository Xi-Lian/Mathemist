#!/bin/bash
# ============================================
# DeepSeek 大模型本地部署脚本
# 适用于 GPU 服务器（16GB显存）
# ============================================

set -e

echo "🚀 开始部署 DeepSeek 大模型..."

# ============================================
# 1. 检查 GPU 环境
# ============================================
echo ""
echo "🔍 步骤 1/6: 检查 GPU 环境..."

if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ 未检测到 NVIDIA GPU 驱动"
    echo "请先安装 NVIDIA 驱动和 CUDA"
    exit 1
fi

echo "✅ GPU 信息:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv

# 检查 CUDA 版本
if command -v nvcc &> /dev/null; then
    echo "✅ CUDA 版本: $(nvcc --version | grep release | awk '{print $5}' | sed 's/,//')"
else
    echo "⚠️  未检测到 CUDA Toolkit，建议安装"
fi

# ============================================
# 2. 选择部署方案
# ============================================
echo ""
echo "📋 步骤 2/6: 选择部署方案"
echo ""
echo "请选择部署方式："
echo "  1) Ollama（推荐 - 简单易用，支持多种模型）"
echo "  2) vLLM（高性能 - 适合高并发场景）"
echo "  3) HuggingFace Transformers（灵活 - 需要手动配置）"
echo ""
read -p "请输入选项 (1/2/3，默认1): " choice
choice=${choice:-1}

# ============================================
# 3. 安装依赖
# ============================================
echo ""
echo "📦 步骤 3/6: 安装依赖..."

case $choice in
    1)
        echo "安装 Ollama..."
        curl -fsSL https://ollama.com/install.sh | sh
        
        # 启动 Ollama 服务
        echo "启动 Ollama 服务..."
        ollama serve &
        sleep 5
        
        # 下载 DeepSeek 模型（根据显存选择）
        echo ""
        echo "📥 步骤 4/6: 下载 DeepSeek 模型..."
        echo ""
        echo "可选模型："
        echo "  1) deepseek-r1:1.5b（超轻量，适合测试）"
        echo "  2) deepseek-r1:7b（推荐 - 平衡性能和速度）"
        echo "  3) deepseek-r1:8b（高质量，需要更多显存）"
        echo ""
        read -p "请选择模型 (1/2/3，默认2): " model_choice
        model_choice=${model_choice:-2}
        
        case $model_choice in
            1) MODEL="deepseek-r1:1.5b" ;;
            2) MODEL="deepseek-r1:7b" ;;
            3) MODEL="deepseek-r1:8b" ;;
            *) MODEL="deepseek-r1:7b" ;;
        esac
        
        echo "下载模型: $MODEL"
        ollama pull $MODEL
        
        # 测试模型
        echo ""
        echo "🧪 测试模型..."
        ollama run $MODEL "你好" < /dev/null
        
        # 配置 Ollama 监听所有接口
        echo ""
        echo "⚙️  配置 Ollama 允许远程访问..."
        sudo systemctl stop ollama || true
        sudo systemctl set-environment OLLAMA_HOST=0.0.0.0:11434
        sudo systemctl start ollama
        
        SERVICE_URL="http://localhost:11434"
        API_ENDPOINT="/api/generate"
        ;;
        
    2)
        echo "安装 vLLM..."
        pip install vllm torch torchvision torchaudio
        
        # 下载模型
        echo ""
        echo "📥 步骤 4/6: 下载 DeepSeek 模型..."
        python3 -c "from transformers import AutoTokenizer; AutoTokenizer.from_pretrained('deepseek-ai/deepseek-r1-distill-qwen-7b')"
        
        # 启动 vLLM 服务
        echo ""
        echo "🚀 启动 vLLM 服务..."
        nohup python3 -m vllm.entrypoints.openai.api_server \
            --model deepseek-ai/deepseek-r1-distill-qwen-7b \
            --tensor-parallel-size 1 \
            --gpu-memory-utilization 0.9 \
            --port 8001 \
            > vllm.log 2>&1 &
        
        echo "等待 vLLM 启动..."
        sleep 30
        
        SERVICE_URL="http://localhost:8001"
        API_ENDPOINT="/v1/completions"
        ;;
        
    3)
        echo "安装 HuggingFace Transformers..."
        pip install transformers torch accelerate
        
        echo ""
        echo "⚠️  请手动配置模型服务"
        echo "参考文档: https://huggingface.co/docs/transformers/main_classes/pipelines"
        exit 0
        ;;
        
    *)
        echo "无效选项"
        exit 1
        ;;
esac

# ============================================
# 5. 配置后端使用本地模型
# ============================================
echo ""
echo "⚙️  步骤 5/6: 配置后端使用本地模型..."

# 创建 .env.local 文件
cat > .env.local << EOF
# 大模型配置
USE_LOCAL_LLM=true
LOCAL_LLM_URL=$SERVICE_URL
LOCAL_LLM_ENDPOINT=$API_ENDPOINT
LOCAL_LLM_MODEL=$MODEL

# 如果需要使用云端 API，取消下面的注释
# DEEPSEEK_API_KEY=your_api_key_here
EOF

echo "✅ 已创建 .env.local 配置文件"

# ============================================
# 6. 更新后端代码
# ============================================
echo ""
echo "🔧 步骤 6/6: 更新后端代码..."

# 检查是否有 LLM 客户端代码
if [ -f "app/core/llm_client.py" ]; then
    echo "检测到 LLM 客户端代码，需要更新以支持本地模型"
    echo "请参考 app/core/llm_client.py 的注释进行配置"
else
    echo "⚠️  未检测到 LLM 客户端代码，请手动配置"
fi

# ============================================
# 完成
# ============================================
echo ""
echo "=========================================="
echo "✅ DeepSeek 大模型本地部署完成！"
echo "=========================================="
echo ""
echo "📊 服务信息："
echo "  - 服务地址: $SERVICE_URL"
echo "  - API 端点: $API_ENDPOINT"
echo "  - 模型名称: $MODEL"
echo ""
echo "📝 下一步："
echo "  1. 检查 .env.local 配置文件"
echo "  2. 更新后端代码以使用本地模型"
echo "  3. 重启后端服务"
echo "  4. 测试 API 调用速度"
echo ""
echo "🔗 测试命令："
if [ "$choice" = "1" ]; then
    echo "  curl http://localhost:11434/api/generate -d '{\"model\": \"$MODEL\", \"prompt\": \"你好\"}'"
elif [ "$choice" = "2" ]; then
    echo "  curl http://localhost:8001/v1/completions -d '{\"model\": \"$MODEL\", \"prompt\": \"你好\"}'"
fi
echo ""
