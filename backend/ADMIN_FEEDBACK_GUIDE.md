# 管理员反馈系统使用指南

## 📋 概述

本文档告诉管理员如何查看、分析和导出用户反馈数据。

**反馈数据存储位置**: `backend/data/user_feedback.json`

---

## ⭐ 方法一：管理员仪表盘（强烈推荐！）

### 这是最简单、最直观的方式！

#### 如何打开
1. 打开文件夹：`d:\Git_Repository\Mathemist\backend`
2. 双击 `feedback_dashboard.html`
3. 自动用浏览器打开

或在浏览器地址栏输入：
```
file:///d:/Git_Repository/Mathemist/backend/feedback_dashboard.html
```

#### 仪表盘功能
| 功能 | 说明 |
|------|------|
| 📊 **实时统计卡片** | 总点赞、总点踩、总反馈、点赞率 |
| 👎 **被点踩资源** | 按点踩次数排序，显示最新反馈 |
| 💡 **改进建议** | 显示所有用户建议，最新的在前 |
| 📊 **资源类型统计** | 各类型资源的点赞/点踩分布 |
| � **一键刷新** | 点击按钮刷新所有数据 |
| 🟢 **连接状态** | 实时显示后端服务状态 |

#### 界面特点
- ✅ 无需安装 - 纯HTML+JavaScript，直接打开
- ✅ 响应式设计 - 支持手机、平板、电脑
- ✅ 美观渐变 - 紫色渐变背景，现代化UI
- ✅ 实时更新 - 自动检查连接，手动刷新数据
- ✅ 空状态提示 - 没有数据时友好提示

---

## � 方法二：直接查看JSON文件（最简单）

### 步骤
1. 打开文件：`d:\Git_Repository\Mathemist\backend\data\user_feedback.json`
2. 用任何文本编辑器或JSON查看器打开

### 数据结构说明

```json
{
  "resource_feedback": {
    "资源ID": [
      {
        "timestamp": "2026-02-25T10:30:00",
        "query": "用户搜索的查询",
        "resource_type": "exercise",
        "is_like": true,
        "dislike_reason": "",
        "metadata": {
          "知识点标签": "指数函数",
          "source_file": "第四章-指数与指数函数/xxx.md"
        }
      }
    ]
  },
  "improvement_suggestions": [
    {
      "timestamp": "2026-02-25T10:35:00",
      "query": "用户搜索的查询",
      "suggestion": "建议内容",
      "contact": "用户联系方式"
    }
  ],
  "statistics": {
    "total_likes": 128,
    "total_dislikes": 32,
    "feedback_by_type": {
      "exercise": { "likes": 80, "dislikes": 20 },
      "课件": { "likes": 30, "dislikes": 8 },
      "教案": { "likes": 18, "dislikes": 4 }
    }
  }
}
```

---

## 🚀 方法三：通过API查看

### 前置条件
后端服务必须正在运行！

如果后端没有运行，在终端执行：
```bash
cd backend
python main.py
```

---

### API 1: 查看统计概览

**访问地址**: `http://localhost:8000/feedback/statistics`

**在浏览器中直接打开**，或用curl/postman访问。

**返回内容**:
- 总点赞数
- 总点踩数
- 各资源类型的点赞/点踩分布

**示例输出**:
```json
{
  "success": true,
  "statistics": {
    "total_likes": 128,
    "total_dislikes": 32,
    "feedback_by_type": {
      "exercise": { "likes": 80, "dislikes": 20 },
      "课件": { "likes": 30, "dislikes": 8 }
    }
  }
}
```

---

### API 2: 查看被点踩最多的资源

**访问地址**: `http://localhost:8000/feedback/disliked?limit=50`

**参数**:
- `limit`: 返回的资源数量（默认50）

**返回内容**:
- 按点踩次数降序排列的资源列表
- 每个资源的详细反馈历史

**用途**:
- 找出哪些资源最有问题
- 分析这些资源的共同点
- 针对性优化检索算法

---

### API 3: 查看改进建议

**访问地址**: `http://localhost:8000/feedback/suggestions?limit=100`

**参数**:
- `limit`: 返回的建议数量（默认100）

**返回内容**:
- 所有用户改进建议
- 最新的建议在最前面

**用途**:
- 直接了解用户需求
- 发现系统的不足
- 规划新功能

---

### API 4: 导出反馈数据

**访问地址**: `http://localhost:8000/feedback/export`

**功能**:
- 自动生成带时间戳的导出文件
- 文件保存在 `backend/data/` 目录

**返回内容**:
```json
{
  "success": true,
  "export_path": "d:\\Git_Repository\\Mathemist\\backend\\data\\feedback_export_20260225_103000.json"
}
```

---

## 📊 数据分析方法

### 1. 找出有问题的主题

**步骤**:
1. 访问 `http://localhost:8000/feedback/disliked`
2. 查看被点踩最多的资源
3. 分析这些资源的共同点：
   - 都来自哪些文件夹？
   - 知识点标签是什么？
   - 用户反馈的原因是什么？

**示例分析**:
- 如果被点踩的资源都来自"第三章-二次函数"，说明用户搜"指数函数"时推了太多二次函数
- 如果被点踩的原因都是"主题不对"，说明主题匹配算法有问题

---

### 2. 分析用户改进建议

**步骤**:
1. 访问 `http://localhost:8000/feedback/suggestions`
2. 阅读所有建议
3. 分类整理：
   - 哪些建议是关于检索准确性的？
   - 哪些建议是关于资源类型的？
   - 哪些建议是关于功能的？

**示例整理**:
- 高频建议1："希望能搜索到更多图像题" → 可以增加图像特征词识别
- 高频建议2："希望能按难度筛选" → 可以添加难度过滤功能

---

### 3. 统计分析

**步骤**:
1. 访问 `http://localhost:8000/feedback/statistics`
2. 查看整体数据：
   - 点赞率 = 总点赞 / (总点赞 + 总点踩)
   - 各资源类型的表现

**关键指标**:
- **点赞率 > 80%**: 表现优秀
- **点赞率 60-80%**: 表现良好
- **点赞率 < 60%**: 需要重点优化

---

## 🔧 方法四：快速测试脚本（命令行）

我为您创建了一个Python脚本，方便您在命令行查看反馈数据！

### 运行测试脚本

在 `backend/` 目录下创建 `test_feedback_api.py`:

```python
import requests
import json

BASE_URL = "http://localhost:8000"

def print_separator(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_statistics():
    print_separator("1. 统计概览")
    response = requests.get(f"{BASE_URL}/feedback/statistics")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_disliked():
    print_separator("2. 被点踩最多的资源")
    response = requests.get(f"{BASE_URL}/feedback/disliked?limit=10")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_suggestions():
    print_separator("3. 改进建议")
    response = requests.get(f"{BASE_URL}/feedback/suggestions?limit=20")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

def test_export():
    print_separator("4. 导出数据")
    response = requests.get(f"{BASE_URL}/feedback/export")
    data = response.json()
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    print("🎯 用户反馈系统 - 管理员测试工具")
    print("="*60)
    
    try:
        test_statistics()
        test_disliked()
        test_suggestions()
        test_export()
        
        print_separator("✅ 所有测试完成！")
    except requests.exceptions.ConnectionError:
        print("\n❌ 错误：无法连接到后端服务！")
        print("请先运行：cd backend ; python main.py")
    except Exception as e:
        print(f"\n❌ 错误：{e}")
```

### 运行测试脚本

```bash
cd backend
python test_feedback_api.py
```

---

## 📈 优化闭环流程

### 步骤1：收集反馈
- 让用户使用前端反馈功能
- 定期查看反馈数据

### 步骤2：分析问题
- 查看被点踩最多的资源
- 分析改进建议
- 找出共性问题

### 步骤3：优化系统
- 根据反馈调整检索算法
- 修复有问题的资源
- 添加用户需要的功能

### 步骤4：验证效果
- 观察点赞率是否提升
- 观察被点踩资源是否减少
- 继续收集反馈

---

## 🎯 常见问题

### Q: 反馈数据会丢失吗？
A: 不会！所有反馈都保存在 `backend/data/user_feedback.json` 文件中，即使重启服务也不会丢失。

### Q: 如何备份反馈数据？
A: 直接复制 `user_feedback.json` 文件即可，或者调用 `/feedback/export` API导出。

### Q: 可以删除错误的反馈吗？
A: 可以！直接编辑 `user_feedback.json` 文件删除对应条目即可。

### Q: 后端服务没运行怎么办？
A: 在 `backend/` 目录下运行 `python main.py` 启动服务。

---

## 📞 技术支持

如有问题，请查看：
1. 后端日志（运行 `python main.py` 的终端）
2. `user_feedback.json` 文件内容
3. API返回的错误信息

---

## 📁 管理员可用的工具总结

| 工具 | 文件位置 | 推荐度 | 说明 |
|------|---------|--------|------|
| ⭐ 管理员仪表盘 | `backend/feedback_dashboard.html` | ⭐⭐⭐⭐⭐ | 最直观，推荐日常使用 |
| 测试脚本 | `backend/test_feedback_api.py` | ⭐⭐⭐ | 命令行查看，适合快速检查 |
| 直接API访问 | 浏览器访问 `http://localhost:8000/feedback/*` | ⭐⭐ | 适合调试 |
| 直接看JSON | `backend/data/user_feedback.json` | ⭐ | 最底层，适合技术人员 |

---

**文档版本**: v2.0  
**最后更新**: 2026-02-25  
**新增**: 管理员仪表盘（`feedback_dashboard.html`）
