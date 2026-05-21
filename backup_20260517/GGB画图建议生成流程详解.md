# GGB 画图建议生成流程详解

## 📋 概述

GGB（GeoGebra）画图建议功能是一个基于 AI 的智能设计顾问系统，能够根据用户输入的数学课题信息，自动生成 GeoGebra 动态图的设计建议和教学指导。

---

## 🔄 完整流程

### 1️⃣ 前端用户输入

**文件**: `frontend/src/components/geometry/CombinedGeometryWorkbench.tsx`

**用户需要填写的信息**：
- **章节**（chapter）：例如 "三角函数"
- **主题**（topic）：例如 "正弦函数图像"
- **教学用途**（teaching_purpose）：例如 "帮助学生理解正弦函数的周期性和相位变化"
- **后端地址**（apiBaseUrl）：默认 "http://localhost:8000"

**触发方式**：
用户点击"获取建议"按钮 → 调用 `handleFetchSuggestions()` 函数

---

### 2️⃣ 前端 API 调用

**请求 URL**：
```
POST http://localhost:8000/ggb/innovation-suggestions
```

**请求体**：
```json
{
  "chapter": "三角函数",
  "topic": "正弦函数图像",
  "teaching_purpose": "帮助学生理解正弦函数的周期性和相位变化"
}
```

**关键代码**（第73-84行）：
```tsx
const response = await fetch(
  `${normalizeBaseUrl(apiBaseUrl)}/ggb/innovation-suggestions`,
  {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      chapter: chapter.trim(),
      topic: topic.trim(),
      teaching_purpose: teachingPurpose.trim(),
    }),
  },
);
```

---

### 3️⃣ 后端 API 路由接收

**文件**: `backend/app/api/routes/ggb.py`

**路由定义**（第33行）：
```python
@router.post("/innovation-suggestions", response_model=InnovationSuggestionResponse)
async def get_innovation_suggestions(request: InnovationSuggestionRequest):
```

**请求模型**（第18-23行）：
```python
class InnovationSuggestionRequest(BaseModel):
    """创新建议请求模型"""
    chapter: str
    topic: str
    teaching_purpose: str
    existing_ggb_info: Optional[str] = None  # 可选参数
```

**处理逻辑**（第44-64行）：
```python
# 调用核心函数生成建议
result = generate_ggb_innovation_suggestions(
    chapter=request.chapter,
    topic=request.topic,
    teaching_purpose=request.teaching_purpose,
    existing_ggb_info=request.existing_ggb_info
)

# 返回成功结果
return InnovationSuggestionResponse(
    status="success",
    data=result
)
```

---

### 4️⃣ 核心业务逻辑

**文件**: `backend/app/core/ggb_design_advisor.py`

**主函数**（第147-179行）：
```python
def generate_ggb_innovation_suggestions(
    chapter: str,
    topic: str,
    teaching_purpose: str,
    existing_ggb_info: Optional[str] = None
) -> Dict[str, Any]:
    """生成GGB创新设计建议的适配函数"""
    advisor = GGBDesignAdvisor()
    
    try:
        suggestions = advisor.generate_simple_suggestions(
            chapter=chapter,
            topic=topic,
            teaching_purpose=teaching_purpose,
            existing_ggb_info=existing_ggb_info
        )
        
        return {
            "suggestions": suggestions
        }
    except Exception as e:
        return advisor._get_error_response(str(e))
```

---

### 5️⃣ AI 提示词构建

**类方法**: `GGBDesignAdvisor.generate_simple_suggestions()`（第28-112行）

**提示词模板**（第47-91行）：
```python
prompt_template = ChatPromptTemplate.from_template("""
你是一位资深的GeoGebra动态数学软件专家和数学教育专家。

请根据以下信息，为GeoGebra动态图生成简洁实用的设计建议：

## 基本信息
- 章节：{chapter}
- 主题：{topic}
- 教学用途：{teaching_purpose}

{existing_info}

## 输出要求

请生成简洁明了的设计建议，格式如下：

# {topic} GeoGebra动态图设计建议

## 设计目标
[用2-3句话说明设计目标]

## 核心设计步骤
1. [第一步，具体操作]
2. [第二步，具体操作]
3. [第三步，具体操作]
...

## 关键交互元素
- [交互元素1，如滑动条、按钮等]
- [交互元素2]
...

## 教学建议
- [教学建议1]
- [教学建议2]
...

注意：
- 语言要简洁，避免冗余
- 步骤要具体可操作
- 突出GeoGebra的动态和交互特性
- 重点关注如何帮助学生理解数学概念

现在，请生成设计建议。
""")
```

**现有信息处理**（第93-100行）：
```python
existing_info = ""
if existing_ggb_info:
    existing_info = f"""
## 现有GGB信息
{existing_ggb_info}

请参考现有信息进行补充和完善。
"""
```

---

### 6️⃣ AI 模型调用

**模型配置**（第102-110行）：
```python
model = self.model_config.get_model("visualization")
chain = prompt_template | model | StrOutputParser()

result = chain.invoke({
    "chapter": chapter,
    "topic": topic,
    "teaching_purpose": teaching_purpose,
    "existing_info": existing_info
})
```

**使用的模型**：
- **提供商**：DeepSeek（默认）或 OpenAI 兼容模式
- **模型名称**：`deepseek-chat`（可配置）
- **温度参数**：0.3（较低，确保输出稳定）
- **最大 token**：默认值（未特别指定）

**模型初始化位置**：`backend/app/core/model_config.py`

---

### 7️⃣ 响应返回

**后端响应格式**：
```json
{
  "status": "success",
  "data": {
    "suggestions": "# 正弦函数图像 GeoGebra动态图设计建议\n\n## 设计目标\n..."
  }
}
```

**前端处理**（第86-98行）：
```tsx
const data = (await response.json().catch(() => ({}))) as SuggestionResponse;

if (!response.ok) {
  throw new Error(`请求失败（${response.status}）`);
}

if (data.status !== "success" || !data.data) {
  throw new Error(data.error || "获取建议失败");
}

const markdown =
  data.data.suggestions?.trim() || "未返回详细建议，请稍后重试。";
setResultMarkdown(markdown);
```

---

### 8️⃣ 前端展示

**显示位置**：右侧 Markdown 渲染区域

**组件**：使用 `MarkdownText` 组件渲染 Markdown 格式的建議

**预期输出格式**：
```markdown
# 正弦函数图像 GeoGebra动态图设计建议

## 设计目标
通过动态可视化帮助学生直观理解正弦函数的周期性、振幅和相位变化。

## 核心设计步骤
1. 创建坐标系：使用"坐标轴"工具建立直角坐标系
2. 绘制基础函数：输入 f(x) = sin(x)
3. 添加滑动条：创建参数 a（振幅）、b（频率）、c（相位）
4. 绑定参数：修改函数为 f(x) = a*sin(b*x + c)
5. 设置动画：为滑动条添加自动播放功能

## 关键交互元素
- 滑动条 a：控制振幅（范围 0-3）
- 滑动条 b：控制频率（范围 0.5-3）
- 滑动条 c：控制相位（范围 -π 到 π）
- 播放按钮：启动/停止动画

## 教学建议
- 先让学生观察静态图像，再引入动态变化
- 引导学生发现参数变化对图像的影响规律
- 鼓励学生自己调整参数，探索不同效果
```

---

## 📦 使用的资源

### 1. AI 模型资源

| 资源类型 | 配置项 | 默认值 | 说明 |
|---------|--------|--------|------|
| LLM 提供商 | `LLM_PROVIDER` | `auto` | auto/deepseek/openai_compatible |
| DeepSeek API Key | `DEEPSEEK_API_KEY` | - | 从 `.env` 文件读取 |
| DeepSeek 模型 | `DEEPSEEK_MODEL` | `deepseek-chat` | 可配置其他模型 |
| 温度参数 | - | `0.3` | 较低温度确保稳定性 |

**配置文件**：`backend/.env`

**示例配置**：
```env
LLM_PROVIDER=auto
DEEPSEEK_API_KEY=sk-b1...2ff16
DEEPSEEK_MODEL=deepseek-chat
```

---

### 2. LangChain 组件

| 组件 | 用途 |
|------|------|
| `ChatPromptTemplate` | 构建提示词模板 |
| `StrOutputParser` | 解析字符串输出 |
| `Chain` | 组合提示词、模型、解析器 |

**导入语句**：
```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
```

---

### 3. FastAPI 组件

| 组件 | 用途 |
|------|------|
| `APIRouter` | 定义 API 路由 |
| `BaseModel` | 定义请求/响应模型 |
| `HTTPException` | 异常处理 |

**导入语句**：
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
```

---

### 4. 前端组件

| 组件 | 文件路径 | 用途 |
|------|----------|------|
| `CombinedGeometryWorkbench` | `frontend/src/components/geometry/CombinedGeometryWorkbench.tsx` | 主界面组件 |
| `Input` | shadcn/ui | 输入框组件 |
| `MarkdownText` | `frontend/src/components/thread/markdown-text.tsx` | Markdown 渲染 |

---

## 🔧 关键技术点

### 1. URL 路径处理（V48.9-V48.10 修复）

**问题**：`apiUrl` 参数可能包含 `/langgraph/math-agent` 后缀

**解决方案**：
```tsx
// 从查询参数或环境变量中提取基础 URL
const baseUrl = apiUrl.replace(/\/langgraph\/math-agent$/, "");
```

**规范**：GGB 接口路径应为 `/ggb/innovation-suggestions`，不应包含 `/langgraph/math-agent` 前缀

---

### 2. Hydration 错误处理（V48.8, V48.11 修复）

**问题**：服务器端和客户端渲染不一致

**解决方案**：
```tsx
// 延迟渲染依赖动态状态的组件
<Input
  value={isMounted ? apiBaseUrl : ""}
  onChange={(e) => setApiBaseUrl(e.target.value)}
/>
```

---

### 3. 错误处理

**后端错误响应**（第114-144行）：
```python
def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
    return {
        "suggestions": f"""
# ❌ GGB动态图设计建议生成失败

抱歉，生成过程中出现错误：**{error_msg}**

## 可能的原因：
1. 网络连接问题，无法访问AI模型
2. API密钥配置错误
3. 输入信息不完整或格式错误

## 建议解决方案：
1. 检查网络连接
2. 确认.env文件中的API密钥配置正确
3. 检查输入信息是否完整
4. 稍后重试或联系管理员
""",
        "error": error_msg
    }
```

**前端错误处理**（第99-104行）：
```tsx
catch (error) {
  const msg =
    error instanceof Error ? error.message : "获取建议失败，请稍后重试。";
  setErrorText(
    `调用后端建议接口失败：${msg}。请确认后端服务与接口已启动。`,
  );
}
```

---

## 🎯 优化建议

### 1. 增强提示词

当前提示词已经比较完善，可以考虑：
- 添加更多学科特定的指导原则
- 提供 GeoGebra 最佳实践案例
- 增加难度分级（初级/中级/高级）

### 2. 缓存机制

对于相同的输入，可以缓存 AI 生成的建议：
```python
import hashlib
cache_key = hashlib.md5(f"{chapter}_{topic}_{teaching_purpose}".encode()).hexdigest()
```

### 3. 异步处理

如果生成时间较长，可以考虑：
- 使用 WebSocket 推送进度
- 实现流式输出（Streaming）
- 添加超时控制

### 4. 多语言支持

当前仅支持中文，可以扩展为：
- 检测用户语言偏好
- 提供多语言提示词模板
- 支持国际化输出

---

## 📊 性能指标

| 指标 | 预期值 | 说明 |
|------|--------|------|
| 响应时间 | 3-10秒 | 取决于 AI 模型响应速度 |
| 成功率 | >95% | 排除网络错误 |
| Token 消耗 | ~500-1500 | 每次请求的 token 数量 |
| 并发能力 | 10-50 QPS | 取决于模型 API 限制 |

---

## 🔍 调试技巧

### 1. 查看后端日志

启动后端时添加调试日志：
```python
print(f"📝 收到 GGB 建议请求:")
print(f"   章节: {chapter}")
print(f"   主题: {topic}")
print(f"   教学用途: {teaching_purpose}")
```

### 2. 查看前端 Network 标签

打开浏览器开发者工具 → Network 标签：
- 检查请求 URL 是否正确
- 检查请求体是否完整
- 检查响应状态码和数据

### 3. 测试 API 直接调用

使用 curl 测试：
```bash
curl -X POST http://localhost:8000/ggb/innovation-suggestions \
  -H "Content-Type: application/json" \
  -d '{
    "chapter": "三角函数",
    "topic": "正弦函数图像",
    "teaching_purpose": "帮助学生理解周期性"
  }'
```

### 4. 查看 API 文档

访问 `http://localhost:8000/docs`，找到 `ggb` 标签下的接口，可以直接在浏览器中测试。

---

## 📝 总结

**GGB 画图建议生成流程**：
1. ✅ 用户在前端填写表单（章节、主题、教学用途）
2. ✅ 前端发送 POST 请求到 `/ggb/innovation-suggestions`
3. ✅ 后端 API 路由接收请求并验证参数
4. ✅ 调用核心函数 `generate_ggb_innovation_suggestions()`
5. ✅ 构建 AI 提示词模板
6. ✅ 调用 DeepSeek AI 模型生成建议
7. ✅ 返回 Markdown 格式的建议
8. ✅ 前端渲染并显示给用户

**使用的资源**：
- 🤖 **AI 模型**：DeepSeek Chat（可配置）
- 🔗 **LangChain**：提示词模板、链式调用
- ⚡ **FastAPI**：API 路由、数据验证
- 🎨 **前端组件**：React + Next.js + shadcn/ui

**关键特性**：
- 🎯 智能推断：根据教学用途生成针对性建议
- 📝 结构化输出：统一的 Markdown 格式
- 🛡️ 错误处理：完善的异常捕获和用户提示
- 🔧 灵活配置：支持多种 AI 模型提供商

这个系统为数学教师提供了一个强大的 GeoGebra 设计辅助工具，帮助他们快速创建高质量的动态数学可视化内容！🎉
