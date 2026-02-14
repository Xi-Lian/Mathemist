# 模块架构说明文档

## 概述

本文档详细说明了重构后的模块架构，包括各模块的职责、接口定义、依赖关系及使用示例。

## 架构设计原则

### 单一职责原则
每个模块只负责一个明确的功能领域，确保功能内聚性。

### 依赖倒置原则
高层模块不依赖低层模块，都依赖于抽象接口。

### 开闭原则
模块对扩展开放，对修改关闭。

## 目录结构

```
backend/app/
├── core/                    # 核心功能模块
│   ├── __init__.py
│   ├── model_config.py      # 模型配置和管理
│   ├── resource_classifier.py  # 资源分类
│   resource_table_parser.py  # 资源汇总表解析
│   ├── vector_database_builder.py # 向量数据库构建
│   ├── resource_retriever.py   # 资源检索
│   ├── intent_analyzer.py      # 意图理解
│   ├── lesson_plan_generator.py # 教案生成
│   ├── visualization_advisor.py # 可视化建议
│   └── response_builder.py     # 响应构建
├── api/                     # API层
│   ├── __init__.py
│   ├── models.py           # API数据模型
│   └── routes/            # 路由模块
│       ├── __init__.py
│       ├── assistants.py     # 助手相关路由
│       ├── threads.py       # 线程相关路由
│       └── runs.py         # 运行相关路由
├── utils/                   # 工具模块
│   ├── __init__.py
│   ├── helpers.py          # 辅助函数
│   └── constants.py        # 常量定义
├── nodes.py                 # 节点定义
├── langgraph_api.py        # API入口
├── state.py                # 状态定义
└── graph.py                # 图定义
```

## 核心模块 (core/)

### 1. model_config.py - 模型配置模块

**职责：**
- 管理所有语言模型的初始化和配置
- 提供统一的模型获取接口
- 实现单例模式管理模型实例

**主要类：**
- `ModelConfig`: 模型配置管理类（单例模式）

**主要方法：**
```python
# 获取DeepSeek语言模型
get_deepseek_model() -> ChatDeepSeek

# 获取Embedding模型
get_embedding_model() -> SentenceTransformer

# 获取ChromaDB客户端
get_chroma_client() -> chromadb.PersistentClient

# 获取智能内容处理器
get_content_processor() -> SmartContentProcessor
```

**使用示例：**
```python
from app.core.model_config import model_config

# 获取模型
llm = model_config.get_deepseek_model()
embedding_model = model_config.get_embedding_model()

# 使用模型
response = llm.invoke("Hello")
```

**依赖：**
- langchain_deepseek
- sentence_transformers
- chromadb
- smart_content_processor

---

### 2. resource_classifier.py - 资源分类模块

**职责：**
- 根据文件路径和内容智能分类资源类型
- 提供关键词匹配和评分机制
- 支持多种资源类型的识别

**主要类：**
- `ResourceClassifier`: 资源分类器

**主要方法：**
```python
# 分类资源
ResourceClassifier.classify(source: str, content: str) -> str
```

**支持的资源类型：**
- `lesson_plan`: 教案资源
- `syllabus`: 教学大纲
- `courseware`: 课件资源
- `lesson_case`: 课例资源
- `ggb`: GGB动态数学资源
- `visualization`: 可视化资源
- `exercise`: 习题资源
- `theory`: 理论卡片资源

**使用示例：**
```python
from app.core.resource_classifier import ResourceClassifier

# 分类资源
resource_type = ResourceClassifier.classify(
    source="/path/to/lesson_plan.md",
    content="这是一个教案..."
)
print(resource_type)  # 输出: lesson_plan
```

**依赖：**
- 无外部依赖（纯逻辑模块）

---

### 3. resource_table_parser.py - 资源汇总表解析模块

**职责：**
- 解析learning_resource文件夹中的markdown表格数据
- 支持多种表格格式（标准markdown表格、Excel导出表格、特殊格式表格）
- 提供统一的资源信息提取接口
- 支持所有资源类型的汇总表解析

**主要类：**
- `ResourceTableParser`: 资源汇总表解析器

**主要方法：**
```python
# 解析markdown表格
parse_markdown_table(content: str) -> List[Dict[str, str]]

# 解析GGB资源汇总表
parse_ggb_table() -> List[Dict[str, str]]

# 解析教学大纲汇总表
parse_syllabus_table() -> List[Dict[str, str]]

# 解析习题资源汇总表
parse_exercise_tables() -> List[Dict[str, str]]

# 解析教案资源汇总表
parse_lesson_plan_tables() -> List[Dict[str, str]]

# 解析理论卡片
parse_theory_cards() -> List[Dict[str, str]]

# 解析课件资源汇总表
parse_courseware_table() -> List[Dict[str, str]]

# 解析课例资源汇总表
parse_lesson_case_table() -> List[Dict[str, str]]

# 解析所有资源汇总表
parse_all_tables() -> Dict[str, List[Dict[str, str]]]

# 格式化资源为搜索文本
format_resource_for_search(resource: Dict[str, str]) -> str

# 获取资源文件名
get_resource_filename(resource: Dict[str, str]) -> Optional[str]
```

**支持的资源类型：**
- `ggb`: GGB动态数学资源
- `syllabus`: 教学大纲
- `exercise`: 习题资源
- `lesson_plan`: 教案资源
- `theory`: 理论卡片资源
- `courseware`: 课件资源
- `lesson_case`: 课例资源

**使用示例：**
```python
from app.core.resource_table_parser import ResourceTableParser

# 初始化解析器
parser = ResourceTableParser("/path/to/learning_resource")

# 解析所有资源汇总表
all_resources = parser.parse_all_tables()

# 访问各类资源
ggb_resources = all_resources["ggb"]
syllabus_resources = all_resources["syllabus"]
exercise_resources = all_resources["exercise"]
courseware_resources = all_resources["courseware"]
lesson_case_resources = all_resources["lesson_case"]

# 格式化资源为搜索文本
search_text = parser.format_resource_for_search(resource)

# 获取资源文件名
filename = parser.get_resource_filename(resource)
```

**依赖：**
- pathlib
- re
- logging

---

### 4. vector_database_builder.py - 向量数据库构建模块

**职责：**
- 基于资源汇总表构建ChromaDB向量数据库
- 使用SentenceTransformer生成文本嵌入向量
- 支持向量数据库的创建、更新和删除
- 提供向量数据库状态检查

**主要类：**
- `VectorDatabaseBuilder`: 向量数据库构建器

**主要方法：**
```python
# 构建向量数据库
build_vector_database(force_rebuild: bool = False) -> bool

# 检查向量数据库是否存在
check_database_exists() -> bool

# 获取ChromaDB客户端
get_chroma_client() -> chromadb.Client

# 获取embedding模型
get_embedding_model() -> SentenceTransformer
```

**使用示例：**
```python
from app.core.vector_database_builder import VectorDatabaseBuilder

# 初始化构建器
builder = VectorDatabaseBuilder("/path/to/learning_resource")

# 检查向量数据库是否存在
if builder.check_database_exists():
    print("向量数据库已存在")
else:
    print("向量数据库不存在")

# 构建向量数据库
success = builder.build_vector_database(force_rebuild=True)

if success:
    print("向量数据库构建成功")
else:
    print("向量数据库构建失败")
```

**依赖：**
- chromadb
- sentence_transformers
- resource_table_parser (资源汇总表解析)
- model_config (模型配置)

---

### 5. resource_retriever.py - 资源检索模块

**职责：**
- 使用ChromaDB进行语义检索
- 根据查询和意图检索相关资源
- 对检索结果进行分类和组织
- 实现习题资源的特殊处理逻辑

**主要类：**
- `ResourceRetriever`: 资源检索器

**主要方法：**
```python
# 检索资源
retrieve(query: str, intent: str = "search", n_results: int = 50) -> Dict[str, Any]
```

**返回结果结构：**
```python
{
    "theory_resources": [...],        # 理论资源
    "lesson_plan_patterns": [...],   # 教案资源
    "exercise_resources": [...],     # 习题资源
    "visualization_examples": [...], # 可视化示例
    "general_resources": [...],      # 通用资源
    "courseware_resources": [...],   # 课件资源
    "lesson_case_resources": [...],  # 课例资源
    "ggb_resources": [...],         # GGB资源
    "syllabus_resources": [...]      # 教学大纲资源
}
```

**使用示例：**
```python
from app.core.resource_retriever import ResourceRetriever

# 检索资源
retriever = ResourceRetriever()
results = retriever.retrieve(
    query="指数函数",
    intent="search",
    n_results=50
)

# 访问结果
lesson_plans = results["lesson_plan_patterns"]
exercises = results["exercise_resources"]
coursewares = results["courseware_resources"]
lesson_cases = results["lesson_case_resources"]
```

**依赖：**
- model_config (模型配置)
- resource_table_parser (资源汇总表解析)
- vector_database_builder (向量数据库构建)
- chromadb (向量数据库)
- sentence_transformers (Embedding模型)

---

### 6. intent_analyzer.py - 意图理解模块

**职责：**
- 分析用户输入，确定用户意图
- 支持基于LLM的意图识别
- 提供关键词匹配作为备用方案

**主要类：**
- `IntentAnalyzer`: 意图分析器

**主要方法：**
```python
# 分析意图
analyze(user_input: str) -> Dict[str, Any]
```

**支持的意图类型：**
- `search`: 资源搜索
- `generate_lesson_plan`: 教案生成
- `visualization`: 可视化建议

**返回结果结构：**
```python
{
    "intent": "generate_lesson_plan",  # 主要意图
    "intents": [                     # 所有意图
        {"type": "generate_lesson_plan", "confidence": 0.9},
        {"type": "visualization", "confidence": 0.8},
        {"type": "search", "confidence": 0.1}
    ],
    "current_step": "intent_understanding",
    "error": None
}
```

**使用示例：**
```python
from app.core.intent_analyzer import IntentAnalyzer

# 分析意图
analyzer = IntentAnalyzer()
result = analyzer.analyze("帮我生成一份指数函数的教案")

print(result["intent"])  # 输出: generate_lesson_plan
```

**依赖：**
- model_config (模型配置)
- langchain (提示词和链)

---

### 7. lesson_plan_generator.py - 教案生成模块

**职责：**
- 根据用户需求和检索到的资源生成教案
- 整合理论依据和优秀教案特征
- 提供结构化的教案输出

**主要类：**
- `LessonPlanGenerator`: 教案生成器

**主要方法：**
```python
# 生成教案
generate(
    user_input: str,
    theory_resources: List[Dict[str, Any]],
    lesson_plan_patterns: List[Dict[str, Any]]
) -> str
```

**使用示例：**
```python
from app.core.lesson_plan_generator import LessonPlanGenerator

# 生成教案
generator = LessonPlanGenerator()
lesson_plan = generator.generate(
    user_input="指数函数教案",
    theory_resources=[...],
    lesson_plan_patterns=[...]
)

print(lesson_plan)
```

**依赖：**
- model_config (模型配置)
- langchain (提示词和链)

---

### 8. visualization_advisor.py - 可视化建议模块

**职责：**
- 根据用户需求和检索到的示例生成可视化设计建议
- 提供专业的GGB动态数学设计指导
- 整合优秀设计示例

**主要类：**
- `VisualizationAdvisor`: 可视化建议器

**主要方法：**
```python
# 生成可视化建议
advise(
    user_input: str,
    visualization_examples: List[Dict[str, Any]]
) -> str
```

**使用示例：**
```python
from app.core.visualization_advisor import VisualizationAdvisor

# 生成建议
advisor = VisualizationAdvisor()
suggestions = advisor.advise(
    user_input="指数函数可视化",
    visualization_examples=[...]
)

print(suggestions)
```

**依赖：**
- model_config (模型配置)
- langchain (提示词和链)

---

### 9. response_builder.py - 响应构建模块

**职责：**
- 根据意图和生成的结果构建最终响应
- 整合教案、可视化建议和检索到的资源
- 提供结构化的响应输出

**主要类：**
- `ResponseBuilder`: 响应构建器

**主要方法：**
```python
# 构建响应
build(state: Dict[str, Any]) -> str
```

**使用示例：**
```python
from app.core.response_builder import ResponseBuilder

# 构建响应
builder = ResponseBuilder()
response = builder.build({
    "intent": "generate_lesson_plan",
    "lesson_plan": "...",
    "retrieved_resources": {...}
})

print(response)
```

**依赖：**
- model_config (模型配置)
- smart_content_processor (内容处理)

---

## API模块 (api/)

### 1. models.py - 数据模型模块

**职责：**
- 定义API请求和响应的数据模型
- 提供数据验证
- 支持Pydantic模型

**主要模型：**
- `AssistantInfo`: 助手信息
- `Thread`: 线程模型
- `Run`: 运行模型
- `Resource`: 资源模型
- `Message`: 消息模型
- 等等...

**使用示例：**
```python
from app.api.models import AssistantInfo, Thread

# 创建助手信息
assistant = AssistantInfo(
    assistant_id="math-agent",
    name="高中数学资源智能体",
    description="..."
)

# 创建线程
thread = Thread(
    thread_id="xxx",
    created_at="2024-01-01T00:00:00Z",
    updated_at="2024-01-01T00:00:00Z"
)
```

**依赖：**
- pydantic

---

### 2. routes/ - 路由模块

#### assistants.py - 助手相关路由

**职责：**
- 处理助手相关的API请求
- 提供助手信息查询接口

**主要端点：**
- `GET /assistants/{assistant_id}`: 获取助手信息
- `GET /assistants/{assistant_id}/graph`: 获取图结构
- `GET /assistants/{assistant_id}/schemas`: 获取模式
- `POST /assistants/search`: 搜索助手
- `GET /assistants`: 列出所有助手
- `GET /info`: 获取信息

**使用示例：**
```bash
# 获取助手信息
curl http://localhost:8000/assistants/math-agent

# 获取图结构
curl http://localhost:8000/assistants/math-agent/graph
```

---

#### threads.py - 线程相关路由

**职责：**
- 处理线程相关的API请求
- 提供线程创建、查询、搜索接口

**主要端点：**
- `POST /threads`: 创建新线程
- `GET /threads/{thread_id}`: 获取线程信息
- `POST /threads/search`: 搜索线程
- `GET /threads`: 列出所有线程

**使用示例：**
```bash
# 创建线程
curl -X POST http://localhost:8000/threads \
  -H "Content-Type: application/json" \
  -d '{"metadata": {"user_id": "123"}}'

# 获取线程信息
curl http://localhost:8000/threads/{thread_id}
```

---

#### runs.py - 运行相关路由

**职责：**
- 处理运行相关的API请求
- 提供运行创建、查询、流式接口

**主要端点：**
- `POST /threads/{thread_id}/runs`: 创建运行（非流式）
- `POST /threads/{thread_id}/runs/stream`: 创建运行（流式）

**使用示例：**
```bash
# 创建运行（非流式）
curl -X POST http://localhost:8000/threads/{thread_id}/runs \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "math-agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]}
  }'

# 创建运行（流式）
curl -X POST http://localhost:8000/threads/{thread_id}/runs/stream \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "math-agent",
    "input": {"messages": [{"role": "user", "content": "Hello"}]}
  }'
```

---

## 工具模块 (utils/)

### 1. helpers.py - 辅助函数模块

**职责：**
- 提供通用的辅助函数
- ID生成
- 数据验证
- 格式化工具

**主要函数：**
```python
# 生成唯一ID
generate_id() -> str

# 获取当前时间戳
get_current_timestamp() -> str

# 安全地获取字典值
safe_get(data: Dict[str, Any], key: str, default: Any = None) -> Any

# 安全地转换为字符串
safe_str(value: Any, default: str = "") -> str

# 检查值是否为空
is_empty(value: Any) -> bool

# 截断文本
truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str

# 格式化百分比
format_percentage(value: float, decimals: int = 1) -> str

# 去重列表
deduplicate_list(items: List[Any], key_func=None) -> List[Any]

# 根据键排序字典列表
sort_by_key(items: List[Dict[str, Any]], key: str, reverse: bool = False) -> List[Dict[str, Any]]

# 合并多个字典
merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]

# 验证邮箱格式
validate_email(email: str) -> bool

# 清理文件名
sanitize_filename(filename: str) -> str

# 格式化文件大小
format_file_size(size_bytes: int) -> str
```

**使用示例：**
```python
from app.utils import generate_id, safe_get, truncate_text

# 生成ID
id = generate_id()

# 安全获取字典值
value = safe_get(data, "key", default="default")

# 截断文本
short_text = truncate_text(long_text, max_length=50)
```

---

### 2. constants.py - 常量定义模块

**职责：**
- 定义项目中使用的常量
- 集中管理配置值

**主要常量：**
```python
# API相关
API_PREFIX = ""
API_TAGS = ["LangGraph API"]

# 助手相关
ASSISTANT_ID = "math-agent"
ASSISTANT_NAME = "高中数学资源智能体"
GRAPH_ID = "math-agent"

# 意图类型
INTENT_SEARCH = "search"
INTENT_GENERATE_LESSON_PLAN = "generate_lesson_plan"
INTENT_VISUALIZATION = "visualization"

# 资源类型
RESOURCE_TYPE_LESSON_PLAN = "lesson_plan"
RESOURCE_TYPE_EXERCISE = "exercise"
# ... 等等

# 状态
STATUS_PENDING = "pending"
STATUS_RUNNING = "running"
STATUS_SUCCESS = "success"
STATUS_ERROR = "error"

# 步骤
STEP_INTENT_UNDERSTANDING = "intent_understanding"
STEP_RESOURCE_RETRIEVAL = "resource_retrieval"
# ... 等等
```

**使用示例：**
```python
from app.utils.constants import ASSISTANT_ID, INTENT_SEARCH

# 使用常量
print(ASSISTANT_ID)  # 输出: math-agent
print(INTENT_SEARCH)  # 输出: search
```

---

## 节点定义 (nodes.py)

**职责：**
- 定义LangGraph工作流的各个节点
- 协调各个核心模块完成工作流

**主要节点：**
```python
# 意图理解节点
intent_understanding_node(state: MathAgentState) -> Dict[str, Any]

# 资源检索节点
resource_retrieval_node(state: MathAgentState) -> Dict[str, Any]

# 教案生成节点
lesson_plan_generation_node(state: MathAgentState) -> Dict[str, Any]

# 可视化建议节点
visualization_suggestions_node(state: MathAgentState) -> Dict[str, Any]

# 响应格式化节点
response_formatting_node(state: MathAgentState) -> Dict[str, Any]
```

**使用示例：**
```python
from app.nodes import intent_understanding_node, resource_retrieval_node

# 在LangGraph中使用
from app.graph import create_math_agent_graph

graph = create_math_agent_graph()
result = await graph.ainvoke({"user_input": "Hello"})
```

---

## API入口 (langgraph_api.py)

**职责：**
- 提供LangGraph API接口
- 协调各个路由模块
- 处理流式和非流式请求

**使用示例：**
```python
from app.langgraph_api import router
from fastapi import FastAPI

app = FastAPI()
app.include_router(router)
```

---

## 模块依赖关系图

```
┌─────────────────────────────────────────────────────────────┐
│                    nodes.py                             │
│              (节点定义和工作流)                          │
└──────────────────┬──────────────────────────────────────┘
                   │
                   │ 依赖
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    core/                               │
│  ┌──────────────┬──────────────┬──────────────┐      │
│  │model_config  │resource_     │intent_       │      │
│  │              │table_parser  │analyzer      │      │
│  └──────────────┴──────────────┴──────────────┘      │
│  ┌──────────────┬──────────────┬──────────────┐      │
│  │vector_      │resource_     │lesson_plan_  │      │
│  │database_    │retriever     │generator     │      │
│  │builder      │              │              │      │
│  └──────────────┴──────────────┴──────────────┘      │
│  ┌──────────────┬──────────────┐                    │
│  │visualization │response_     │                    │
│  │_advisor     │builder       │                    │
│  └──────────────┴──────────────┘                    │
└──────────────────┬───────────────────────────────────────┘
                   │
                   │ 依赖
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    utils/                               │
│  ┌──────────────┬──────────────┐                    │
│  │helpers       │constants     │                    │
│  └──────────────┴──────────────┘                    │
└──────────────────┬───────────────────────────────────────┘
                   │
                   │ 依赖
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                    api/                                │
│  ┌──────────────┬──────────────┬──────────────┐      │
│  │models        │routes/       │              │      │
│  │              │assistants    │              │      │
│  │              │threads       │              │      │
│  │              │runs          │              │      │
│  └──────────────┴──────────────┴──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 模块依赖关系说明

#### nodes.py
- 依赖所有core模块
- 协调各个核心模块完成工作流

#### core/model_config.py
- 无内部依赖
- 提供模型配置服务

#### core/resource_table_parser.py
- 无内部依赖
- 提供资源汇总表解析服务

#### core/vector_database_builder.py
- 依赖 resource_table_parser
- 依赖 model_config
- 提供向量数据库构建服务

#### core/resource_retriever.py
- 依赖 vector_database_builder
- 依赖 model_config
- 提供资源检索服务

#### core/intent_analyzer.py
- 依赖 model_config
- 提供意图分析服务

#### core/lesson_plan_generator.py
- 依赖 model_config
- 提供教案生成服务

#### core/visualization_advisor.py
- 依赖 model_config
- 提供可视化建议服务

#### core/response_builder.py
- 依赖 model_config
- 提供响应构建服务

#### utils/
- 无内部依赖
- 提供通用工具函数

#### api/
- 依赖 utils/
- 提供API接口

---

## 重构优势

### 1. 职责清晰
每个模块都有明确的职责边界，易于理解和维护。

### 2. 可测试性
模块独立，便于单元测试和集成测试。

### 3. 可扩展性
新增功能只需添加新模块，不影响现有代码。

### 4. 可维护性
代码组织清晰，便于定位和修复问题。

### 5. 可复用性
核心功能模块可在其他项目中复用。

---

## 新增模块说明

### resource_table_parser.py - 资源汇总表解析模块

**新增原因：**
- 项目需要从learning_resource文件夹中读取多种类型的资源汇总表
- 这些汇总表以markdown格式存储，包含资源的元数据信息
- 需要一个专门的模块来解析这些表格数据

**主要功能：**
- 解析GGB资源汇总表
- 解析教学大纲汇总表
- 解析习题资源汇总表
- 解析教案资源汇总表
- 解析理论卡片
- 解析课件资源汇总表（新增）
- 解析课例资源汇总表（新增）
- 支持多种表格格式（标准markdown表格、Excel导出表格、特殊格式表格）

**解决的问题：**
- 统一了资源汇总表的解析逻辑
- 支持了课件和课例资源的解析
- 修复了Excel导出表格的解析问题
- 提供了统一的资源信息提取接口

### vector_database_builder.py - 向量数据库构建模块

**新增原因：**
- 项目需要基于资源汇总表构建向量数据库
- 需要使用SentenceTransformer生成文本嵌入向量
- 需要管理ChromaDB的创建、更新和删除

**主要功能：**
- 基于资源汇总表构建ChromaDB向量数据库
- 使用SentenceTransformer生成文本嵌入向量
- 支持向量数据库的创建、更新和删除
- 提供向量数据库状态检查

**解决的问题：**
- 统一了向量数据库的构建逻辑
- 提供了向量数据库的自动构建和更新机制
- 支持了所有资源类型的向量化和索引
- 提供了向量数据库状态检查功能

**与resource_retriever.py的关系：**
- vector_database_builder负责构建向量数据库
- resource_retriever使用向量数据库进行检索
- 两者通过ChromaDB客户端进行交互

---

## 资源类型支持

### 完整的资源类型列表

1. **ggb** - GGB动态数学资源
   - 文件位置：learning_resource/ggb/
   - 汇总表：ggb信息.md
   - 特殊处理：显示文件名

2. **syllabus** - 教学大纲
   - 文件位置：learning_resource/教学大纲/
   - 汇总表：函数教学大纲.md
   - 特殊处理：显示章节和教学任务

3. **exercise** - 习题资源
   - 文件位置：learning_resource/习题/
   - 汇总表：各章节文件夹中的markdown文件
   - 特殊处理：文字习题显示完整内容，图片习题显示文件名

4. **lesson_plan** - 教案资源
   - 文件位置：learning_resource/教案/
   - 汇总表：各章节文件夹中的markdown文件
   - 特殊处理：显示标题和内容

5. **theory** - 理论卡片资源
   - 文件位置：learning_resource/教案/理论卡片/
   - 汇总表：理论卡片文件夹中的markdown文件
   - 特殊处理：不推送给用户，仅用于教案生成

6. **courseware** - 课件资源（新增）
   - 文件位置：learning_resource/课件/
   - 汇总表：课件汇总（必修一2.3-5.md
   - 特殊处理：显示文件名

7. **lesson_case** - 课例资源（新增）
   - 文件位置：learning_resource/课例视频/
   - 汇总表：优秀课例视频信息汇总.md
   - 特殊处理：显示视频文件名/网址

### 资源检索流程

1. 用户输入查询（如"指数函数资源"）
2. ResourceRetriever接收查询
3. 使用SentenceTransformer生成查询向量
4. 在ChromaDB向量数据库中进行语义检索
5. 对检索结果按资源类型分类
6. 返回各类资源列表

### 资源显示策略

- **理论资源**：不推送给用户，仅用于教案生成
- **习题资源**：文字习题显示完整内容，图片习题显示文件名
- **GGB资源**：显示文件名
- **课件资源**：显示文件名
- **课例资源**：显示视频文件名/网址
- **教学大纲**：显示章节和教学任务
- **教案资源**：显示标题和内容

---

## 最佳实践

### 1. 导入规范
```python
# 推荐：从模块导入具体的类或函数
from app.core.model_config import ModelConfig
from app.core.resource_classifier import ResourceClassifier

# 不推荐：导入整个模块
from app.core import model_config
```

### 2. 错误处理
```python
# 推荐：使用try-except捕获异常
try:
    result = analyzer.analyze(user_input)
except Exception as e:
    logger.error(f"分析失败: {e}")
    return get_default_result()
```

### 3. 日志记录
```python
# 推荐：使用logging模块
import logging
logger = logging.getLogger(__name__)

logger.info("开始处理请求")
logger.error(f"处理失败: {error}")
```

### 4. 类型提示
```python
# 推荐：使用类型提示
def analyze(user_input: str) -> Dict[str, Any]:
    ...
```

---

## 迁移指南

### 从旧代码迁移到新模块

#### 1. 模型配置
```python
# 旧代码
from app.nodes import get_model, get_embedding_model

# 新代码
from app.core.model_config import model_config

llm = model_config.get_model()
embedding = model_config.get_embedding_model()
```

#### 2. 资源分类
```python
# 旧代码
from app.nodes import classify_resource

# 新代码
from app.core.resource_classifier import ResourceClassifier

resource_type = ResourceClassifier.classify(source, content)
```

#### 3. 资源检索
```python
# 旧代码
from app.nodes import retrieve_resources

# 新代码
from app.core.resource_retriever import ResourceRetriever

retriever = ResourceRetriever()
results = retriever.retrieve(query, intent)
```

#### 4. 意图理解
```python
# 旧代码
from app.nodes import intent_understanding_node

# 新代码
from app.core.intent_analyzer import IntentAnalyzer

analyzer = IntentAnalyzer()
result = analyzer.analyze(user_input)
```

#### 5. 资源汇总表解析
```python
# 新代码
from app.core.resource_table_parser import ResourceTableParser

parser = ResourceTableParser("/path/to/learning_resource")
all_resources = parser.parse_all_tables()
```

#### 6. 向量数据库构建
```python
# 新代码
from app.core.vector_database_builder import VectorDatabaseBuilder

builder = VectorDatabaseBuilder("/path/to/learning_resource")
success = builder.build_vector_database(force_rebuild=True)
```

---

## 总结

重构后的模块架构遵循单一职责原则，将原来的两个大文件拆分为多个职责明确的小模块。这种架构提高了代码的可维护性、可测试性和可扩展性，为未来的功能扩展奠定了良好的基础。
