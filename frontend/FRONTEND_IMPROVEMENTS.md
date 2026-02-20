# 前端改进建议文档

## 项目概述

本项目采用**对话式界面**设计，所有功能都应在同一个聊天界面中通过对话交互完成，不创建独立的功能页面。

---

## 已实现的功能 ✅

### 核心功能
- [x] 基础聊天界面
- [x] LangGraph API 连接
- [x] 消息发送与展示
- [x] 多轮对话历史记录
- [x] 主题切换（亮色/深色）
- [x] 语言切换（中文/英文）
- [x] 文件上传（PDF/图片）
- [x] Artifact 产物展示区域
- [x] 聊天历史侧边栏

---

## 待实现的功能 ❌

### 1. 智能协编教案功能

#### 功能描述
在聊天界面中集成多阶段协编教案功能，通过对话引导用户完成教案编写。

#### 需要修改的文件
- `src/locales/zh-CN.ts` - 添加协编相关翻译
- `src/components/thread/messages/ai.tsx` - 增强AI消息组件
- 新建 `src/components/thread/messages/collaborative-stage.tsx` - 协编阶段展示组件
- 新建 `src/lib/api/collaborative.ts` - 协编API封装

#### 具体实现
1. **识别协编意图**
   - 在聊天中检测"协编教案"、"一起备课"等关键词
   - 自动启动协编会话

2. **阶段进度展示**
   - 在消息中显示可视化进度条
   - 显示当前阶段：初始 → 教学目标 → 教学框架 → 教案草稿 → 完成
   - 每个阶段可编辑和确认

3. **API调用**
   - `POST /collaborative/session/start` - 开始会话
   - `POST /collaborative/session/continue` - 继续会话
   - `GET /collaborative/session/{session_id}` - 获取会话状态

---

### 2. GGB创新设计建议功能

#### 功能描述
在聊天中展示GGB（GeoGebra）创新设计建议，包括框架设计、创新点、个性化指南等。后端生成简单的GGB图形框架代码，前端通过GeoGebra URL参数打开预设图形，用户可以在此基础上根据建议完善。

#### 需要修改的文件
- `src/locales/zh-CN.ts` - 添加GGB相关翻译
- `src/components/thread/messages/ai.tsx` - 增强AI消息组件
- 新建 `src/components/thread/messages/ggb-suggestions.tsx` - GGB建议展示组件
- 新建 `src/lib/api/ggb.ts` - GGB API封装
- 新建 `src/lib/ggb-utils.ts` - GeoGebra URL生成工具

#### 具体实现
1. **识别GGB需求**
   - 检测"GGB设计"、"可视化建议"、"GeoGebra"等关键词
   - 引导用户输入章节、教材、主题、教学目的

2. **后端返回内容**
   - 框架设计：用卡片形式展示基础框架
   - 创新点：列表形式展示创新建议
   - 个性化指南：分点说明
   - 教学应用：展示如何在课堂中使用
   - **ggb_base64**：简单图形框架的Base64编码（.ggb文件内容）
   - **ggb_commands**：GeoGebra命令列表（可选，用于构造图形）

3. **聊天界面中的结构化展示**
   - 展示创新建议内容
   - **添加"在GeoGebra中打开基础图形"按钮**
   - 点击按钮使用GeoGebra URL参数打开预设图形

4. **GeoGebra URL构造方式**
   - 方式1：使用Base64编码的.ggb文件
     ```
     https://www.geogebra.org/classic?ggbBase64={base64_content}
     ```
   - 方式2：使用GeoGebra命令
     ```
     https://www.geogebra.org/classic?command=A=(1,2);B=(3,4);Segment(A,B)
     ```
   - 方式3：传递JSON配置
     ```
     https://www.geogebra.org/classic?json={...}
     ```

5. **API调用**
   - `POST /ggb/innovation-suggestions` - 获取创新建议和基础图形

---

### 3. 用户系统功能

#### 功能描述
添加用户认证、偏好设置和教案历史记录功能。

#### 需要修改的文件
- `src/locales/zh-CN.ts` - 添加用户系统翻译
- `src/components/thread/index.tsx` - 添加用户菜单入口
- 新建 `src/components/user-menu.tsx` - 用户菜单组件
- 新建 `src/components/user-preferences-dialog.tsx` - 偏好设置对话框
- 新建 `src/lib/api/user.ts` - 用户API封装
- 新建 `src/providers/User.tsx` - 用户状态管理

#### 具体实现
1. **用户入口**
   - 在界面右上角添加用户头像/登录按钮
   - 点击展开用户菜单

2. **用户菜单功能**
   - 用户信息展示
   - 偏好设置（教学风格、常用教材等）
   - 查看教案历史记录
   - 退出登录

3. **教案历史记录**
   - 在聊天历史侧边栏中，按用户分组显示
   - 显示历史记录的标签、备注等信息

4. **API调用**
   - `POST /users/create` - 创建用户
   - `GET /users/{user_id}` - 获取用户信息
   - `PUT /users/preferences` - 更新偏好
   - `POST /users/lesson-plan-history` - 创建历史记录
   - `GET /users/{user_id}/lesson-plan-history` - 获取历史列表
   - `GET /users/{user_id}/lesson-plan-history/{history_id}` - 获取历史详情

---

### 4. 教案导出功能

#### 功能描述
在教案生成完成后，提供多格式导出功能。

#### 需要修改的文件
- `src/locales/zh-CN.ts` - 添加导出相关翻译
- `src/components/thread/messages/ai.tsx` - 在教案消息中添加导出按钮
- 新建 `src/components/export-dialog.tsx` - 导出选项对话框
- 新建 `src/lib/api/export.ts` - 导出API封装

#### 具体实现
1. **导出按钮**
   - 在AI生成的教案消息下方添加"导出"按钮
   - 按钮位置在消息底部右侧

2. **导出选项**
   - 点击按钮弹出对话框
   - 选择导出格式：Markdown、HTML、DOCX、PDF
   - 输入文件名（可选）
   - 填写元数据（作者、日期等，可选）

3. **API调用**
   - `POST /lesson-plan/export` - 导出教案
   - 显示下载链接或直接触发下载

---

### 5. 资源展示优化

#### 功能描述
优化理论卡片、习题资源等在聊天中的展示方式。

#### 需要修改的文件
- `src/locales/zh-CN.ts` - 添加资源展示翻译
- `src/components/thread/messages/ai.tsx` - 增强AI消息组件
- 新建 `src/components/thread/messages/resource-card.tsx` - 资源卡片组件
- 新建 `src/components/thread/messages/exercise-card.tsx` - 习题卡片组件

#### 具体实现
1. **理论卡片展示**
   - 卡片形式展示标题和摘要
   - 点击展开查看完整内容
   - 支持搜索和筛选（在聊天历史侧边栏）

2. **习题资源展示**
   - 卡片形式展示题目
   - 默认隐藏答案/解析
   - 点击"显示答案"展开解析
   - 显示题目来源和难度

3. **优秀实践库**
   - 预留展示框架
   - 暂时显示"敬请期待"提示

---

## 文件结构建议

```
frontend/src/
├── components/
│   ├── thread/
│   │   └── messages/
│   │       ├── collaborative-stage.tsx    [新建]
│   │       ├── ggb-suggestions.tsx        [新建]
│   │       ├── resource-card.tsx          [新建]
│   │       └── exercise-card.tsx          [新建]
│   ├── user-menu.tsx                       [新建]
│   ├── user-preferences-dialog.tsx         [新建]
│   └── export-dialog.tsx                   [新建]
├── lib/
│   ├── api/
│   │   ├── collaborative.ts                 [新建]
│   │   ├── ggb.ts                           [新建]
│   │   ├── user.ts                          [新建]
│   │   └── export.ts                        [新建]
│   └── ggb-utils.ts                        [新建] - GeoGebra URL生成工具
├── providers/
│   └── User.tsx                            [新建]
└── locales/
    └── zh-CN.ts                            [修改]
```

---

## 实现优先级建议（按难度排序）

### 🟢 第一阶段（简单，1-2天可完成）
**实现难度：低**
1. **教案导出功能** - 只需要添加按钮和对话框，API调用简单
2. **习题资源展示优化** - 显示题目，点击展开答案

### 🟡 第二阶段（中等，3-5天可完成）
**实现难度：中等**
3. **理论卡片展示** - 卡片形式展示，支持展开/收起
4. **GGB创新设计建议** - 在聊天中展示建议，生成带预设图形的GeoGebra链接
5. **用户系统基础（登录/头像）** - 简单的用户菜单，偏好设置弹窗

### 🟠 第三阶段（较难，1周以上）
**实现难度：较高**
6. **智能协编教案功能** - 多阶段对话管理，进度展示
7. **用户系统高级功能** - 完整的历史记录管理，状态持久化

---

## 难度评估说明

### 简单功能（推荐先做）
- **教案导出**：只需要在现有消息组件加个按钮，弹出对话框选择格式，调用API即可
- **习题展示**：创建简单的卡片组件，默认隐藏答案，点击展开

### 中等功能（可以第二阶段做）
- **理论卡片**：类似习题卡片，但内容更多
- **GGB创新设计建议**：在聊天中展示结构化建议，使用GeoGebra URL参数打开预设的基础图形
- **用户基础**：简单的localStorage存储用户信息，不需要后端完整认证

### 复杂功能（可以暂缓或分阶段）
- **协编教案**：需要管理复杂的对话状态和阶段进度
- **用户高级功能**：需要完整的登录认证、状态管理、历史记录同步

### 用户系统简化版
- 只用localStorage存储用户偏好
- 不需要后端登录认证
- 历史记录存在本地浏览器

### 协编教案简化版
- 先不做完整的阶段管理
- 在聊天中通过自然对话引导用户
- 用简单的消息提示当前进度

---

## 注意事项

1. **保持对话式体验**：所有功能都应通过自然对话触发，不使用复杂的导航菜单
2. **渐进式增强**：可以先实现基础版本，后续逐步完善
3. **国际化支持**：所有新增文本都需要同时添加中文和英文翻译
4. **响应式设计**：确保在不同屏幕尺寸下都有良好的体验
5. **错误处理**：API调用失败时要有友好的错误提示
