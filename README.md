# Mathemist - 高中数学资源智能体

基于 AI 的高中数学教学辅助系统，提供教案生成、资源检索、可视化设计建议等功能。

## 📋 项目简介

Mathemist 是一个基于 LangGraph 和 LangChain 构建的智能教学辅助系统，专为高中数学教育设计。系统通过语义检索技术从丰富的教学资源库中提取相关内容，结合大语言模型生成高质量的教学设计方案和可视化建议。

## 🎯 核心功能

### 1. 教案生成
- 基于用户需求自动生成完整的高中数学教案
- 参考优秀教案共性特征
- 符合教学大纲要求
- 包含教学目标、重难点、教学过程等完整内容

### 2. 资源检索
- 基于 ChromaDB 的语义检索
- 支持教案、习题、教学大纲、GGB 资源等多类型检索
- 智能分类和相关性排序

### 3. 可视化设计建议
- 提供 GeoGebra 动态数学设计建议
- 包含构建步骤、交互设计、教学应用场景
- 基于优秀设计示例进行泛化

## 🏗️ 项目架构

```
┌─────────────────────────────────────────────────────────┐
│                   用户界面层                      │
│          (Next.js + React + Tailwind)            │
└────────────────────┬────────────────────────────────┘
                     │ HTTP/WebSocket
┌────────────────────▼────────────────────────────────┐
│                   API服务层                       │
│            (FastAPI + LangServe)                │
└────────────────────┬────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐    ┌────────▼────────┐
│   智能体处理层    │    │   知识库层       │
│ (LangGraph +      │    │  (ChromaDB)     │
│  LangChain)       │    │                 │
└────────┬─────────┘    └─────────────────┘
         │
  ┌──────┴──────┐
  │             │
┌─▼────────┐  ┌─▼──────────┐
│ LLM服务层  │  │  学习资源库  │
│(DeepSeek) │  │  (教案/习题/ │
└───────────┘  │   教学大纲/  │
              │   GGB资源)   │
              └──────────────┘
```

## 📁 项目结构

```
Mathemist/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── graph.py         # LangGraph 状态机定义
│   │   ├── nodes.py         # 节点处理逻辑
│   │   └── state.py        # 状态定义
│   ├── scripts/
│   │   └── ingest.py       # 向量数据库构建脚本
│   ├── main.py              # FastAPI 应用入口
│   ├── requirements.txt      # Python 依赖
│   └── .env               # 后端环境变量配置
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── app/            # Next.js App Router
│   │   ├── components/     # React 组件
│   │   ├── providers/      # React Context Providers
│   │   ├── hooks/          # 自定义 Hooks
│   │   ├── lib/            # 工具函数库
│   │   └── locales/        # 国际化配置
│   ├── package.json        # Node.js 依赖
│   └── .env              # 前端环境变量配置
├── learning_resource/          # 学习资源库
│   ├── 教案/             # 教案资源
│   ├── 习题/             # 习题库
│   ├── 教学大纲/          # 教学大纲
│   └── ggb/              # GeoGebra 资源
└── README.md                 # 项目说明文档
```

## 🚀 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- pnpm 或 npm

### 后端设置

1. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

2. **配置环境变量**

复制 `backend/.env` 文件并配置以下变量：
```env
DEEPSEEK_API_KEY=your-api-key-here
HOST=0.0.0.0
PORT=8000
CORS_ORIGINS=*
LOG_LEVEL=INFO
```

3. **构建知识库**
```bash
python scripts/ingest.py
```

4. **启动后端服务**
```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

### 前端设置

1. **安装依赖**
```bash
cd frontend
pnpm install
```

2. **配置环境变量**

复制 `frontend/.env` 文件并配置以下变量：
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/langserve/math-agent
NEXT_PUBLIC_ASSISTANT_ID=math_agent_graph
LANGSMITH_API_KEY=
```

3. **启动前端服务**
```bash
pnpm dev
```

服务将在 `http://localhost:3000` 启动

## 📚 学习资源

项目包含丰富的高中数学教学资源：

### 教案资源
- 函数概念与性质
- 指数与对数函数
- 三角函数
- 幂函数
- 函数应用

### 习题库
- 按章节组织的习题
- 题目目录和答案目录

### 教学大纲
- 完整的教学任务说明
- 教学提示与学业要求

### GGB 资源
- 动态数学演示
- 函数图象可视化
- 二分法演示等

## 🔧 技术栈

### 后端
- **Web 框架**: FastAPI
- **状态机**: LangGraph
- **LLM 框架**: LangChain
- **模型**: DeepSeek
- **向量数据库**: ChromaDB
- **Embedding**: SentenceTransformer

### 前端
- **框架**: Next.js 15
- **UI 库**: React 19
- **样式**: Tailwind CSS
- **状态管理**: React Context
- **SDK**: @langchain/langgraph-sdk
- **国际化**: 自定义 I18n Provider

## 📡 API 端点

### 健康检查
```http
GET /health
```

### 模型状态
```http
GET /models/status
```

### 调用智能体
```http
POST /math-agent/invoke
Content-Type: application/json

{
  "user_input": "请生成关于函数单调性的教案",
  "chat_history": [],
  "context": {}
}
```

### 流式调用
```http
POST /math-agent/stream
```

## 🔐 环境变量说明

### 后端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | 必填 |
| `HOST` | 服务监听地址 | 0.0.0.0 |
| `PORT` | 服务端口 | 8000 |
| `CORS_ORIGINS` | 允许的跨域源 | * |
| `LOG_LEVEL` | 日志级别 | INFO |

### 前端环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | http://localhost:8000/langserve/math-agent |
| `NEXT_PUBLIC_ASSISTANT_ID` | 助手 ID | math_agent_graph |
| `LANGSMITH_API_KEY` | LangSmith API 密钥 | 可选 |

## 🧪 测试

### 后端测试

```bash
# 测试健康检查
curl http://localhost:8000/health

# 测试模型状态
curl http://localhost:8000/models/status

# 测试智能体调用
curl -X POST http://localhost:8000/math-agent/invoke \
  -H "Content-Type: application/json" \
  -d '{"user_input": "测试"}'
```

### 前端测试

访问 `http://localhost:3000` 并在界面中输入测试内容。

## 📝 开发指南

### 添加新的节点

1. 在 `backend/app/nodes.py` 中定义节点函数
2. 在 `backend/app/graph.py` 中添加节点
3. 定义节点间的边和路由逻辑

### 添加新的资源类型

1. 将资源文件放入 `learning_resource/` 对应目录
2. 在 `backend/app/nodes.py` 的 `classify_resource` 函数中添加分类逻辑
3. 重新运行 `python scripts/ingest.py` 构建知识库

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👥 作者

数智师小队

## 📞 联系方式

如有问题，请提交 Issue 或联系项目维护者。
