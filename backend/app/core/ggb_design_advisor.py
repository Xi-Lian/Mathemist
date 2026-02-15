"""
GeoGebra动态数学设计建议模块

职责：
- 基于现有GGB资源信息，智能生成GeoGebra动态图的设计步骤
- 提供可视化设计原则和指导
- 根据教学用途生成具体的设计建议
- 整合教育理论支持，确保设计原则的科学性

依赖：
- model_config (模型配置)
- langchain (提示词和链)
"""

from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


class GGBDesignAdvisor:
    """GeoGebra动态数学设计顾问"""
    
    def __init__(self):
        """初始化GGB设计顾问"""
        self.model_config = model_config
        self.design_principles = self._get_design_principles()
        self.theoretical_basis = self._get_theoretical_basis()
    
    def generate_design_suggestions(
        self,
        chapter: str,
        textbook: str,
        ggb_filename: str,
        teaching_purpose: str,
        existing_steps: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成GGB动态图设计建议
        
        Args:
            chapter: 章节
            textbook: 教材
            ggb_filename: GGB文件名
            teaching_purpose: 教学用途
            existing_steps: 现有的演示步骤（如果有）
        
        Returns:
            包含设计建议的字典
        """
        print(f"\n====================================")
        print(f"🎨 GGB动态图设计建议生成")
        print(f"📚 章节: {chapter}")
        print(f"📖 教材: {textbook}")
        print(f"📁 文件名: {ggb_filename}")
        print(f"🎯 教学用途: {teaching_purpose}")
        
        try:
            # 生成设计步骤
            design_steps = self._generate_design_steps(
                chapter, textbook, ggb_filename, teaching_purpose, existing_steps
            )
            
            # 生成设计原则说明
            principle_explanation = self._explain_design_principles(
                chapter, teaching_purpose
            )
            
            # 生成理论依据
            theoretical_support = self._generate_theoretical_support(
                chapter, teaching_purpose
            )
            
            # 生成创新点
            innovation_points = self._generate_innovation_points(
                chapter, teaching_purpose, ggb_filename
            )
            
            # 生成教学建议
            teaching_suggestions = self._generate_teaching_suggestions(
                chapter, teaching_purpose
            )
            
            print(f"✅ 设计建议生成成功")
            
            return {
                "design_steps": design_steps,
                "principle_explanation": principle_explanation,
                "theoretical_support": theoretical_support,
                "innovation_points": innovation_points,
                "teaching_suggestions": teaching_suggestions,
                "metadata": {
                    "chapter": chapter,
                    "textbook": textbook,
                    "ggb_filename": ggb_filename,
                    "teaching_purpose": teaching_purpose
                }
            }
            
        except Exception as e:
            print(f"❌ 设计建议生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
    def _generate_design_steps(
        self,
        chapter: str,
        textbook: str,
        ggb_filename: str,
        teaching_purpose: str,
        existing_steps: Optional[str]
    ) -> str:
        """
        生成GeoGebra动态图的设计步骤
        
        Args:
            chapter: 章节
            textbook: 教材
            ggb_filename: GGB文件名
            teaching_purpose: 教学用途
            existing_steps: 现有的演示步骤
        
        Returns:
            设计步骤文本
        """
        prompt_template = ChatPromptTemplate.from_template("""
你是一位资深的GeoGebra动态数学软件专家和数学教育专家，拥有10年以上的GeoGebra教学应用经验。

请根据以下信息，为GeoGebra动态图生成详细的创建步骤和设计建议：

## 基本信息
- 章节：{chapter}
- 教材：{textbook}
- GGB文件名：{ggb_filename}
- 教学用途：{teaching_purpose}

{existing_steps_info}

## 设计原则

### 1. 化静为动原则
- 将静态的数学概念转化为动态的可视化过程
- 通过动画、拖动、参数变化等方式展示数学关系
- 让学生通过观察动态变化理解数学本质

### 2. 化抽象为具体原则
- 将抽象的数学概念用具体的图形表示
- 通过几何直观帮助学生理解代数关系
- 利用可视化降低认知负荷

### 3. 交互性原则
- 设计可拖动的点、可调节的参数
- 让学生通过操作探索数学规律
- 提供即时反馈，增强学习体验

### 4. 渐进性原则
- 从简单到复杂，逐步展示数学概念
- 通过分步动画引导学生思考
- 避免一次性展示过多信息

### 5. 美观性原则
- 使用合适的颜色、线条粗细、字体大小
- 保持界面简洁，避免信息过载
- 突出重点，弱化次要元素

## 输出要求

请按照以下格式输出GeoGebra动态图的设计步骤：

```markdown
# 《{ggb_filename}》GeoGebra动态图设计步骤

## 一、设计目标

根据教学用途"{teaching_purpose}"，本动态图的设计目标是：
[详细说明设计目标，包括要展示的数学概念、关系、规律等]

**📌 设计原则应用：**
- 化静为动：[说明如何将静态概念转化为动态过程]
- 化抽象为具体：[说明如何将抽象概念可视化]
- 交互性：[说明如何设计交互元素]
- 渐进性：[说明如何分步展示]
- 美观性：[说明如何保证界面美观]

---

## 二、前期准备

### 1. 数学素材准备
- [列出需要的数学公式、函数、几何图形等]
- [说明这些素材的数学意义]

### 2. GeoGebra工具准备
- [列出需要使用的GeoGebra工具，如：输入框、滑动条、按钮、文本等]
- [说明每个工具的作用]

---

## 三、详细设计步骤

### 步骤1：创建基础图形
#### 1.1 操作步骤
[详细说明如何在GeoGebra中创建基础图形，包括具体的命令、参数设置等]

#### 1.2 设计要点
[说明这一步的设计要点和注意事项]

#### 1.2 可视化效果
[描述这一步完成后的可视化效果]

---

### 步骤2：添加动态元素
#### 2.1 操作步骤
[详细说明如何添加动态元素，如滑动条、动画等]

#### 2.2 设计要点
[说明动态元素的设计要点]

#### 2.3 可视化效果
[描述动态效果]

---

### 步骤3：设置交互功能
#### 3.1 操作步骤
[详细说明如何设置交互功能，如拖动、点击等]

#### 3.2 设计要点
[说明交互功能的设计要点]

#### 3.3 用户体验
[描述用户交互的体验]

---

### 步骤4：添加辅助元素
#### 4.1 操作步骤
[详细说明如何添加辅助元素，如文本、标注、颜色等]

#### 4.2 设计要点
[说明辅助元素的设计要点]

#### 4.3 美化效果
[描述美化后的效果]

---

### 步骤5：测试与优化
#### 5.1 测试要点
[列出需要测试的功能和效果]

#### 5.2 优化建议
[提供优化建议]

---

## 四、创新点设计

### 创新点1：[创新点名称]
- **设计思路：**[说明创新点的设计思路]
- **实现方法：**[说明如何实现]
- **教学价值：**[说明教学价值]

### 创新点2：[创新点名称]
- **设计思路：**[说明创新点的设计思路]
- **实现方法：**[说明如何实现]
- **教学价值：**[说明教学价值]

---

## 五、教学应用建议

### 1. 课前准备
[说明课前需要做的准备]

### 2. 课堂使用
[说明课堂使用的方法和技巧]

### 3. 学生活动
[设计学生可以参与的活动]

### 4. 课后延伸
[提供课后延伸活动建议]

---

## 六、注意事项

### 技术注意事项
[列出技术方面的注意事项]

### 教学注意事项
[列出教学方面的注意事项]

### 常见问题及解决
[列出常见问题及解决方法]

---

## 七、扩展建议

### 1. 功能扩展
[提供功能扩展的建议]

### 2. 应用拓展
[提供应用拓展的建议]

### 3. 变式设计
[提供变式设计的建议]

---

## 八、设计总结

### 设计亮点
[总结本动态图的设计亮点]

### 适用场景
[说明适用的教学场景]

### 教学效果预期
[预期达到的教学效果]

---
```

## 重要提醒

1. **步骤要具体可操作**：每个步骤都要有具体的操作说明，包括GeoGebra命令、参数设置等
2. **突出动态效果**：重点说明如何实现动态效果，如动画、拖动、参数变化等
3. **体现教学价值**：每个设计都要说明其教学价值，如何帮助学生理解数学概念
4. **符合设计原则**：确保设计符合"化静为动、化抽象为具体"的原则
5. **注重用户体验**：考虑学生的使用体验，设计直观、易用的界面

现在，请根据以上要求，生成详细的GeoGebra动态图设计步骤。
""")

        # 准备现有步骤信息
        existing_steps_info = ""
        if existing_steps:
            existing_steps_info = f"""
## 现有演示步骤

{existing_steps}

请参考现有步骤，进行补充和完善。
"""
        else:
            existing_steps_info = """
## 现有演示步骤

暂无现有演示步骤，请根据教学用途和设计原则，从头开始设计。
"""
        
        # 获取模型
        model = self.model_config.get_model("visualization")
        
        # 构建链
        chain = prompt_template | model | StrOutputParser()
        
        # 调用模型生成设计步骤
        design_steps = chain.invoke({
            "chapter": chapter,
            "textbook": textbook,
            "ggb_filename": ggb_filename,
            "teaching_purpose": teaching_purpose,
            "existing_steps_info": existing_steps_info
        })
        
        return design_steps
    
    def _explain_design_principles(
        self,
        chapter: str,
        teaching_purpose: str
    ) -> str:
        """
        解释设计原则
        
        Args:
            chapter: 章节
            teaching_purpose: 教学用途
        
        Returns:
            设计原则说明文本
        """
        return f"""
## 设计原则说明

根据章节"{chapter}"和教学用途"{teaching_purpose}"，本动态图设计遵循以下原则：

### 1. 化静为动原则
**核心思想：** 将静态的数学概念转化为动态的可视化过程
**应用方式：** 通过动画、拖动、参数变化等方式展示数学关系
**教学价值：** 帮助学生理解数学概念的形成过程和变化规律

### 2. 化抽象为具体原则
**核心思想：** 将抽象的数学概念用具体的图形表示
**应用方式：** 通过几何直观帮助学生理解代数关系
**教学价值：** 降低认知负荷，提高理解效率

### 3. 交互性原则
**核心思想：** 让学生通过操作探索数学规律
**应用方式：** 设计可拖动的点、可调节的参数
**教学价值：** 增强学习体验，培养探究能力

### 4. 渐进性原则
**核心思想：** 从简单到复杂，逐步展示数学概念
**应用方式：** 通过分步动画引导学生思考
**教学价值：** 避免信息过载，符合认知规律

### 5. 美观性原则
**核心思想：** 保持界面简洁，突出重点
**应用方式：** 使用合适的颜色、线条粗细、字体大小
**教学价值：** 提高学习兴趣，减少视觉干扰
"""
    
    def _generate_theoretical_support(
        self,
        chapter: str,
        teaching_purpose: str
    ) -> str:
        """
        生成理论依据
        
        Args:
            chapter: 章节
            teaching_purpose: 教学用途
        
        Returns:
            理论依据文本
        """
        return """
## 理论依据

### 1. 认知负荷理论
**核心观点：** 人的工作记忆容量有限，过多的信息会增加认知负荷
**应用指导：** 通过可视化降低外在认知负荷，提高学习效率
**具体应用：** 使用动态图将抽象概念具体化，减少不必要的认知负担

### 2. 双重编码理论
**核心观点：** 视觉和言语两个通道同时处理信息可以提高记忆和理解
**应用指导：** 结合视觉图像和语言解释，增强学习效果
**具体应用：** 动态图配合文字说明，实现双重编码

### 3. 建构主义学习理论
**核心观点：** 学习者通过主动建构知识来理解世界
**应用指导：** 提供交互式学习环境，让学生主动探索
**具体应用：** 通过拖动、调节参数等交互操作，让学生主动建构数学概念

### 4. 具身认知理论
**核心观点：** 认知与身体经验密切相关
**应用指导：** 通过身体动作和操作体验来促进学习
**具体应用：** 让学生通过操作动态图，获得身体经验，加深理解

### 5. 可视化学习理论
**核心观点：** 可视化可以促进深度学习和理解
**应用指导：** 使用适当的可视化工具展示抽象概念
**具体应用：** GeoGebra动态图作为可视化工具，展示数学概念的本质
"""
    
    def _generate_innovation_points(
        self,
        chapter: str,
        teaching_purpose: str,
        ggb_filename: str
    ) -> str:
        """
        生成创新点
        
        Args:
            chapter: 章节
            teaching_purpose: 教学用途
            ggb_filename: GGB文件名
        
        Returns:
            创新点文本
        """
        return f"""
## 创新点

根据章节"{chapter}"和教学用途"{teaching_purpose}"，本动态图设计包含以下创新点：

### 创新点1：动态参数调节
- **设计思路：** 通过滑动条实时调节参数，观察图形变化
- **实现方法：** 使用GeoGebra的滑动条功能，将参数与图形关联
- **教学价值：** 让学生直观感受参数对函数图像的影响，理解函数性质

### 创新点2：多视角展示
- **设计思路：** 从不同角度展示数学概念，形成全面理解
- **实现方法：** 设计多个视图或多个动态图，展示不同方面
- **教学价值：** 帮助学生建立多角度的思维模式

### 创新点3：交互式探究
- **设计思路：** 设计探究任务，让学生通过操作发现规律
- **实现方法：** 设置问题链，引导学生操作动态图并回答问题
- **教学价值：** 培养学生的探究能力和数学思维

### 创新点4：实时反馈
- **设计思路：** 操作后立即显示结果，提供即时反馈
- **实现方法：** 使用GeoGebra的动态文本功能，实时显示计算结果
- **教学价值：** 增强学习体验，及时纠正错误理解

### 创新点5：分层展示
- **设计思路：** 根据学生水平，提供不同层次的展示
- **实现方法：** 设计基础版、进阶版等不同版本
- **教学价值：** 满足不同层次学生的学习需求
"""
    
    def _generate_teaching_suggestions(
        self,
        chapter: str,
        teaching_purpose: str
    ) -> str:
        """
        生成教学建议
        
        Args:
            chapter: 章节
            teaching_purpose: 教学用途
        
        Returns:
            教学建议文本
        """
        return f"""
## 教学建议

根据章节"{chapter}"和教学用途"{teaching_purpose}"，提供以下教学建议：

### 1. 课前准备
- 熟悉GeoGebra动态图的操作方法
- 准备相关的数学背景知识
- 设计引导问题和探究任务
- 准备备用方案（如软件无法使用时的替代方案）

### 2. 课堂使用
- **引入阶段：** 使用动态图创设情境，激发学习兴趣
- **探究阶段：** 引导学生操作动态图，发现数学规律
- **总结阶段：** 使用动态图回顾总结，巩固知识
- **应用阶段：** 使用动态图解决实际问题，提升应用能力

### 3. 学生活动
- **观察活动：** 让学生观察动态图的变化，记录观察结果
- **操作活动：** 让学生亲自操作动态图，体验数学概念
- **探究活动：** 设计探究任务，让学生通过操作发现规律
- **讨论活动：** 组织学生讨论观察结果和发现

### 4. 课后延伸
- 提供动态图文件，让学生课后继续探索
- 设计拓展任务，让学生应用所学知识
- 鼓励学生自主设计动态图，培养创新能力
- 收集学生反馈，优化动态图设计

### 5. 注意事项
- 不要过度依赖动态图，要与传统教学方法结合
- 注意控制使用时间，避免学生注意力分散
- 确保动态图的设计符合教学目标，不要为了动态而动态
- 关注学生的操作体验，及时提供帮助和指导
"""
    
    def _get_design_principles(self) -> Dict[str, str]:
        """
        获取设计原则
        
        Returns:
            设计原则字典
        """
        return {
            "化静为动": "将静态的数学概念转化为动态的可视化过程",
            "化抽象为具体": "将抽象的数学概念用具体的图形表示",
            "交互性": "设计可拖动的点、可调节的参数",
            "渐进性": "从简单到复杂，逐步展示数学概念",
            "美观性": "使用合适的颜色、线条粗细、字体大小"
        }
    
    def _get_theoretical_basis(self) -> Dict[str, str]:
        """
        获取理论依据
        
        Returns:
            理论依据字典
        """
        return {
            "认知负荷理论": "人的工作记忆容量有限，过多的信息会增加认知负荷",
            "双重编码理论": "视觉和言语两个通道同时处理信息可以提高记忆和理解",
            "建构主义学习理论": "学习者通过主动建构知识来理解世界",
            "具身认知理论": "认知与身体经验密切相关",
            "可视化学习理论": "可视化可以促进深度学习和理解"
        }
    
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应字典
        """
        return {
            "design_steps": f"""
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

---
""",
            "principle_explanation": "",
            "theoretical_support": "",
            "innovation_points": "",
            "teaching_suggestions": "",
            "metadata": {},
            "error": error_msg
        }


# 向后兼容的函数接口
def ggb_design_advisor_node(state) -> Dict[str, Any]:
    """
    GGB设计建议节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含GGB设计建议的更新状态
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 提取检索到的GGB资源
    ggb_resources = []
    
    if isinstance(state, dict):
        retrieved_resources = state.get('retrieved_resources', {})
        ggb_resources = retrieved_resources.get('ggb', [])
    
    # 如果没有GGB资源，返回空结果
    if not ggb_resources:
        return {
            "ggb_design_suggestions": None,
            "current_step": "ggb_design_advisor",
            "error": "未找到相关GGB资源"
        }
    
    # 生成设计建议
    advisor = GGBDesignAdvisor()
    all_suggestions = []
    
    for ggb_resource in ggb_resources[:3]:  # 最多处理前3个GGB资源
        suggestion = advisor.generate_design_suggestions(
            chapter=ggb_resource.get('chapter', ''),
            textbook=ggb_resource.get('textbook', ''),
            ggb_filename=ggb_resource.get('title', ''),
            teaching_purpose=ggb_resource.get('content', ''),
            existing_steps=ggb_resource.get('metadata', {}).get('演示步骤', '')
        )
        all_suggestions.append(suggestion)
    
    return {
        "ggb_design_suggestions": all_suggestions,
        "current_step": "ggb_design_advisor",
        "error": None
    }
