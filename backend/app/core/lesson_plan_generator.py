"""
教案生成模块

职责：
- 根据用户需求和检索到的资源生成教案
- 整合理论依据和优秀教案特征
- 提供结构化的教案输出
- 明确标注理论依据的使用场景和作用

依赖：
- model_config (模型配置)
- langchain (提示词和链)
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


class LessonPlanGenerator:
    """教案生成器"""
    
    def __init__(self):
        """初始化教案生成器"""
        self.model_config = model_config
        self.prompt_template = self._create_prompt_template()
    
    def generate(
        self, 
        user_input: str, 
        theory_resources: List[Dict[str, Any]],
        lesson_plan_patterns: List[Dict[str, Any]]
    ) -> str:
        """
        生成教案
        
        Args:
            user_input: 用户需求
            theory_resources: 理论资源列表
            lesson_plan_patterns: 优秀教案示例列表
        
        Returns:
            生成的教案文本
        """
        print(f"\n====================================")
        print(f"📝 教案生成开始")
        print(f"📝 用户需求: {user_input}")
        print(f"📚 理论资源: {len(theory_resources)}条")
        print(f"📄 教案示例: {len(lesson_plan_patterns)}条")
        
        try:
            # 准备输入数据
            theory_text = self._format_theory_resources(theory_resources)
            patterns_text = self._format_lesson_plan_patterns(lesson_plan_patterns)
            
            # 获取模型
            model = self.model_config.get_model("lesson_plan")
            
            # 构建链
            chain = self.prompt_template | model | StrOutputParser()
            
            # 调用模型生成教案
            lesson_plan = chain.invoke({
                "user_input": user_input,
                "theory_resources": theory_text,
                "lesson_plan_patterns": patterns_text
            })
            
            print(f"✅ 教案生成成功，长度: {len(lesson_plan)}字符")
            
            return lesson_plan
            
        except Exception as e:
            print(f"❌ 教案生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
    def _format_theory_resources(self, resources: List[Dict[str, Any]]) -> str:
        """
        格式化理论资源，提供清晰的理论信息
        
        Args:
            resources: 理论资源列表
        
        Returns:
            格式化后的文本
        """
        if not resources:
            return "暂无相关理论资源"
        
        formatted = []
        for i, resource in enumerate(resources, 1):
            title = resource.get("title", f"理论{i}")
            content = resource.get("content", "")
            source = resource.get("source", "")
            
            # 提取核心观点和教学启发
            core_view = self._extract_section(content, "核心观点")
            teaching_inspiration = self._extract_section(content, "教学启发")
            applicable_links = self._extract_section(content, "适用环节")
            application_case = self._extract_section(content, "应用案例")
            
            formatted.append(f"""
【理论卡片{i}】{title}

📌 核心观点：
{core_view if core_view else content[:500]}

💡 教学启发：
{teaching_inspiration if teaching_inspiration else "请根据理论核心观点提炼教学启发"}

🎯 适用环节：
{applicable_links if applicable_links else "适用于教学全过程"}

📖 应用案例：
{application_case if application_case else "请结合具体教学内容设计应用场景"}

---
""")
        
        return "\n".join(formatted)
    
    def _extract_section(self, content: str, section_name: str) -> str:
        """
        从内容中提取特定章节
        
        Args:
            content: 完整内容
            section_name: 章节名称
        
        Returns:
            提取的章节内容
        """
        import re
        pattern = rf"\*\*{section_name}\*\*\s*\n(.*?)(?=\n\*\*|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""
    
    def _format_lesson_plan_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """
        格式化教案示例，突出优秀教案的共性特征
        
        Args:
            patterns: 教案示例列表
        
        Returns:
            格式化后的文本
        """
        if not patterns:
            return "暂无优秀教案示例"
        
        formatted = []
        for i, pattern in enumerate(patterns, 1):
            title = pattern.get("title", f"教案{i}")
            content = pattern.get("content", "")
            
            # 提取关键信息
            formatted.append(f"""
【优秀教案示例{i}】{title}

{content[:800] if len(content) > 800 else content}

---
""")
        
        return "\n".join(formatted)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"""
# ❌ 教案生成失败

抱歉，教案生成过程中出现错误：**{error_msg}**

## 可能的原因：
1. 网络连接问题，无法访问AI模型
2. API密钥配置错误
3. 理论资源或教案示例加载失败

## 建议解决方案：
1. 检查网络连接
2. 确认.env文件中的API密钥配置正确
3. 稍后重试或联系管理员

---
"""
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建教案生成的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一位资深的高中数学教学设计专家，拥有20年的一线教学经验和深厚的教育理论基础。

## 任务要求

请根据以下信息，生成一个**高质量、理论依据充分、结构清晰**的高中数学教案：

### 📋 用户需求
{user_input}

### 📚 可用的教育理论资源
{theory_resources}

### 📖 优秀教案的共性特征
{lesson_plan_patterns}

---

## 🎯 教案设计要求

### 一、整体结构要求
请按照以下结构组织教案，每个部分都要清晰标注理论依据：

```markdown
# 《[课题名称》教学设计

## 一、教学目标设计

### 1. 知识与技能目标
[具体描述学生应该掌握的知识点和技能]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导目标设计**

### 2. 过程与方法目标
[描述学生通过什么过程、运用什么方法学习]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导过程设计**

### 3. 情感态度与价值观目标
[描述学生在情感、态度、价值观方面的发展]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导情感目标设计**

### 4. 核心素养目标
明确列出**数学抽象、逻辑推理、数学运算、直观想象、数学建模**等核心素养
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导素养培养**

---

## 二、教学重难点分析

### 1. 教学重点
[列出本课的核心概念、性质、方法]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何帮助确定重点**

### 2. 教学难点
[分析学生可能遇到的困难，如抽象思维、概念理解等]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何帮助突破难点**

---

## 三、教学方法与策略

### 1. 教学方法
[列出本课采用的主要教学方法，如探究式教学、合作学习等]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论支持该方法的理由**

### 2. 教学手段
[列出教学工具，如GeoGebra、PPT、智慧黑板等]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导技术整合**

---

## 四、教学过程设计

### 环节一：情境导入（5分钟）
#### 1. 创设情境
[描述具体的生活情境或实际问题]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导情境创设**

#### 2. 提出问题
[设计启发性问题链]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导问题设计**

#### 3. 激发兴趣
[说明如何激发学生的学习动机]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导动机激发**

---

### 环节二：新知探究（15分钟）
#### 1. 自主探究
[设计学生自主探究活动]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导探究设计**

#### 2. 小组合作
[设计小组讨论和合作学习活动]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导合作学习**

#### 3. 教师引导
[说明教师的引导方式和脚手架搭建]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导教师角色**

---

### 环节三：典例分析（10分钟）
#### 1. 典型例题
[设计典型例题，体现核心概念和方法]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导例题选择**

#### 2. 解题思路
[分析解题思路和方法]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导思路分析**

#### 3. 易错点辨析
[指出常见错误和注意事项]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导易错点辨析**

---

### 环节四：跟踪训练（8分钟）
#### 1. 基础训练
[设计基础练习题，巩固基本概念]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导基础训练设计**

#### 2. 综合应用
[设计综合应用题，提升应用能力]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导综合应用设计**

#### 3. 分层作业
[设计分层作业，满足不同层次学生需求]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导分层设计**

---

### 环节五：课堂小结（5分钟）
#### 1. 知识梳理
[梳理本课的知识结构和要点]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导知识梳理**

#### 2. 方法提炼
[提炼数学思想方法]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导方法提炼**

#### 3. 反思评价
[引导学生进行自我反思和评价]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导反思评价**

---

### 环节六：作业布置（2分钟）
#### 1. 基础作业
[布置基础巩固作业]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导作业设计**

#### 2. 拓展作业
[布置拓展延伸作业]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导拓展设计**

---

## 五、板书设计

[设计结构化的板书，包括知识区、典例区、方法区]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导板书设计**

---

## 六、教学反思

### 1. 预期效果
[预期本课的教学效果]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何预测教学效果**

### 2. 可能的问题
[预测可能出现的问题和应对策略]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导问题应对**

### 3. 改进方向
[提出教学改进的方向]
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导教学改进**

---

## 七、理论依据使用总结

### 📚 本教案使用的理论依据汇总

| 理论依据 | 应用环节 | 具体作用 |
|---------|---------|---------|
| [理论卡片X：理论名称] | [环节名称] | [说明该理论在该环节的具体作用] |
| [理论卡片X：理论名称] | [环节名称] | [说明该理论在该环节的具体作用] |
| ... | ... | ... |

### 🎯 理论依据使用亮点

1. **体现"依据理论，有理论可依"的特色**：本教案在设计过程中，充分运用了教育理论，每个教学环节都有明确的理论支撑。
2. **理论与实践的有机结合**：理论依据不是简单的罗列，而是与具体的教学设计紧密结合，体现了理论对实践的指导作用。
3. **理论选择的针对性**：根据不同的教学环节和教学目标，选择了最合适的理论依据，体现了理论应用的灵活性。

---
```

### 二、理论依据引用要求

#### 1. 引用格式
在每个教学环节的设计说明后，使用以下格式标注理论依据：

```markdown
**📌 理论依据：[理论卡片X：理论名称] - 说明该理论如何指导本环节设计**
```

#### 2. 引用原则
- **具体性**：理论依据引用必须具体，不能泛泛而谈
- **针对性**：每个理论依据都要针对具体的教学环节和设计
- **实用性**：说明理论如何指导教学设计，体现理论的应用价值
- **多样性**：合理使用多种理论，体现理论的综合运用

#### 3. 理论依据说明要求
在引用理论依据时，必须说明：
- 该理论的核心观点是什么
- 该理论如何指导本环节的教学设计
- 该理论在本环节中的具体作用是什么

### 三、优秀教案共性特征要求

请在教案设计中充分体现以下优秀教案的共性特征：

#### 1. 教学目标设计
- ✅ 目标明确，紧扣核心内容
- ✅ 核心素养导向突出（数学抽象、逻辑推理、数学运算、直观想象、数学建模）
- ✅ 目标分层清晰，涵盖多个维度，体现层次性

#### 2. 教学重难点把握
- ✅ 突出"关系"与"应用"，重点围绕核心概念、性质及其在实际问题中的应用
- ✅ 难点聚焦抽象思维与思想方法

#### 3. 教学结构设计
- ✅ 流程完整，环节清晰："情境导入/预习导入→新知探究→典例分析→跟踪训练→课堂小结→作业布置"
- ✅ 符合认知发展规律：体现"感知→理解→应用→反思"的学习路径
- ✅ 整体衔接性强：注重与前后知识的衔接

#### 4. 教学内容与方法
- ✅ 情境导入贴近生活：采用实际情境引入课题
- ✅ 强调探究式学习：设置问题链、小组讨论、自主归纳
- ✅ 典例与训练配套精准：实现"讲---练---评"一体化
- ✅ 分层递进，覆盖全面：满足不同层次学生需求
- ✅ 思想方法显化：强调数学思想方法的渗透（数形结合、分类讨论、化归转化、从特殊到一般、函数与方程、数学建模）

#### 5. 教学工具与资源
- ✅ 多媒体与信息技术辅助教学：GeoGebra、几何画板、PPT、智慧黑板
- ✅ 板书与练习系统清晰：结构化板书，典例解析、跟踪训练、达标检测、分层作业

#### 6. 教学评价与反馈
- ✅ 当堂检测与反馈及时
- ✅ 作业设计呼应课堂：基础巩固+拓展延伸
- ✅ 教学反思常态化

#### 7. 学生主体与互动
- ✅ 以学生为中心："学生自主探究+小组合作+教师引导"
- ✅ 语言启发性强：注重启发性提问
- ✅ 关注认知难点与易错点：专项辨析与强化

### 四、用户需求融入要求

请确保教案设计充分响应用户的具体需求：
- 仔细分析用户需求中的关键词和要求
- 将用户需求融入到教案的各个环节设计中
- 在适当的地方说明如何满足用户需求

---

## 📌 重要提醒

1. **理论依据是教案的灵魂**：请在每个环节都明确标注理论依据，说明理论如何指导教学设计
2. **理论与实践结合**：理论依据不是装饰，而是真正指导教学设计的依据
3. **突出"依据理论，有理论可依"的特色**：这是本教案的核心亮点
4. **结构清晰，排版美观**：使用Markdown格式，确保教案易读、美观
5. **内容详实，可操作性强**：教案要具体、详细，具有实际可操作性

现在，请根据以上要求，生成一个高质量、理论依据充分、结构清晰的高中数学教案。
""")


# 向后兼容的函数接口
def lesson_plan_generation_node(state) -> Dict[str, Any]:
    """
    教案生成节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含教案的更新状态
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 提取检索到的资源
    lesson_plan_patterns = []
    
    if isinstance(state, dict):
        retrieved_resources = state.get('retrieved_resources', {})
        lesson_plan_patterns = retrieved_resources.get('lesson_plan_patterns', [])
    
    # 从向量数据库获取理论资源
    theory_resources = []
    try:
        from .resource_retriever import ResourceRetriever
        retriever = ResourceRetriever()
        theory_resources = retriever.get_theory_resources()
        print(f"📚 从向量数据库获取理论资源: {len(theory_resources)}条")
    except Exception as e:
        print(f"⚠️  获取理论资源失败: {str(e)}")
    
    # 生成教案
    generator = LessonPlanGenerator()
    lesson_plan = generator.generate(user_input, theory_resources, lesson_plan_patterns)
    
    return {
        "lesson_plan": lesson_plan,
        "current_step": "lesson_plan_generation",
        "error": None
    }
