from .._shared import *


class _CreatePromptTemplateMixin:
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建意图理解的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一个高中数学教育智能助手的意图理解模块。

请仔细分析用户的输入，判断用户的主要需求和次要需求。

## 重要原则

1. **精准识别用户需求**：不要过度扩展，准确识别用户真正需要什么
2. **避免过度输出**：只输出用户明确需要的资源类型，不要一股脑输出所有资源
3. **优先级明确**：明确区分主要需求和次要需求

## 意图类型说明

1. **search（资源搜索）**：
   - 用户想要查找特定的资源（习题、教案、课件等）
   - 用户询问某个知识点的相关资源
   - 用户想要了解某个主题的教学内容
   - 例如："查找指数函数习题"、"三角函数的教学大纲"

2. **generate_lesson_plan（教案生成）**：
   - 用户明确要求生成教案或教学设计
   - 用户想要备课或教学计划
   - 用户询问如何设计某个知识点的教学
   - 用户提出对现有教案的修改意见
   - 例如："生成指数函数的教案"、"帮我设计三角函数的教学"、"我觉得教学目标太简单了"、"能不能增加一些应用层面的目标"

3. **visualization（可视化建议/GGB设计）**：
   - 用户明确要求GGB动态图设计建议
   - 用户想要可视化设计或动态数学演示
   - 用户询问如何用GeoGebra制作动态图
   - 例如："生成二次函数的GGB动态图设计"、"如何用GeoGebra展示函数单调性"

## 用户输入分析要求

请分析用户输入，判断：
1. **主要需求**：用户最想要什么？
2. **次要需求**：用户可能还需要什么（但不要过度扩展）？
3. **资源类型**：用户明确提到了哪些资源类型？
4. **具体内容**：用户关注的是哪个知识点或主题？

## 输出格式

请输出一个JSON对象，包含以下字段：
- primary_intent: 主要意图
- user_needs: 用户的具体需求描述（1-2句话）
- resource_types: 用户明确提到的资源类型列表（不要过度推断）
- intents: 一个数组，包含所有可能的意图及其置信度，格式为[{{"type": "意图类型", "confidence": 置信度}}]

## 严格输出要求（必须遵守）

- 只能输出 JSON 对象本身
- 不要输出 Markdown 代码块（不要使用 ```json 或 ```）
- 不要输出任何解释、前缀、后缀、注释
- 输出必须以 `{{` 开始，以 `}}` 结束

## 示例

### 示例1
用户输入："查找指数函数习题"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找指数函数相关的习题资源", "resource_types": ["习题"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例2
用户输入："生成指数函数的教案"
输出：
{{"primary_intent": "generate_lesson_plan", "user_needs": "用户想要生成指数函数的教案", "resource_types": ["教案"], "intents": [{{"type": "generate_lesson_plan", "confidence": 0.95}}, {{"type": "search", "confidence": 0.2}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例3
用户输入："生成二次函数的GGB动态图设计"
输出：
{{"primary_intent": "visualization", "user_needs": "用户想要生成二次函数的GGB动态图设计建议", "resource_types": ["GGB"], "intents": [{{"type": "visualization", "confidence": 0.95}}, {{"type": "search", "confidence": 0.2}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}]}}

### 示例4
用户输入："帮我查找指数函数资源"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找指数函数相关的各种教学资源", "resource_types": ["资料"], "intents": [{{"type": "search", "confidence": 0.9}}, {{"type": "generate_lesson_plan", "confidence": 0.2}}, {{"type": "visualization", "confidence": 0.2}}]}}

### 示例5
用户输入："给我指数函数的资料"
输出：
{{"primary_intent": "search", "user_needs": "用户想要获取指数函数相关的所有教学资料", "resource_types": ["资料"], "intents": [{{"type": "search", "confidence": 0.9}}, {{"type": "generate_lesson_plan", "confidence": 0.2}}, {{"type": "visualization", "confidence": 0.2}}]}}

### 示例6
用户输入："给我幂函数的习题"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找幂函数相关的习题资源", "resource_types": ["习题"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例7
用户输入："帮我找抛物线的教案"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找抛物线相关的教案资源", "resource_types": ["教案"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例8
用户输入："帮我推荐指数函数、对数函数和幂函数的教案"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找指数函数、对数函数和幂函数相关的教案资源", "resource_types": ["教案"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例9
用户输入："有没有关于函数零点的教案"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找函数零点相关的教案资源", "resource_types": ["教案"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例10
用户输入："给我推荐一些函数应用的教案"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找函数应用相关的教案资源", "resource_types": ["教案"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例11
用户输入："来几道函数选择题"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找函数相关的选择题习题资源", "resource_types": ["习题"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

### 示例12
用户输入："来一些三角函数的习题"
输出：
{{"primary_intent": "search", "user_needs": "用户想要查找三角函数相关的习题资源", "resource_types": ["习题"], "intents": [{{"type": "search", "confidence": 0.95}}, {{"type": "generate_lesson_plan", "confidence": 0.1}}, {{"type": "visualization", "confidence": 0.1}}]}}

## 特殊说明

- **重要**：当用户使用"找"、"推荐"、"给"、"有没有"、"帮我找"、"帮我推荐"、"来几道"、"来一些"等词语时，即使提到"教案"，也应该识别为**search**意图，因为用户是在查找已有资源
- 只有当用户明确使用"生成"、"设计"、"写"、"创作"等词语时，才识别为**generate_lesson_plan**意图
- 当用户说"资料"或"资源"时，表示用户想要所有类型的教学资源（习题、教案、课件、GGB、教学大纲等）
- 当用户明确指定某种资源类型时（如"习题"、"教案"），只返回该类型
- 不要过度推断用户需求，只输出用户明确提到的资源类型

用户输入：{user_input}

请根据以上要求，输出JSON格式的分析结果。
""")


# 向后兼容的函数接口
