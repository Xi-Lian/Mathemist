"""
GeoGebra动态数学设计建议模块

职责：
- 基于现有GGB资源信息，智能生成GeoGebra动态图的设计步骤
- 提供可视化设计原则和指导
- 根据教学用途生成具体的设计建议
- 整合教育理论支持，确保设计原则的科学性
- 利用 GGB 信息表和教学大纲作为背景资源

依赖：
- model_config (模型配置)
- langchain (提示词和链)
- ggb_resource_retriever (GGB 资源检索器)
"""

from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config
from .ggb_resource_retriever import get_ggb_retriever


class GGBDesignAdvisor:
    """GeoGebra动态数学设计顾问"""
    
    def __init__(self):
        """初始化GGB设计顾问"""
        self.model_config = model_config
    
    def generate_simple_suggestions(
        self,
        chapter: str,
        topic: str,
        teaching_purpose: str,
        existing_ggb_info: Optional[str] = None
    ) -> str:
        """
        生成简洁的GGB设计建议
        
        Args:
            chapter: 章节
            topic: 主题
            teaching_purpose: 教学用途
            existing_ggb_info: 现有GGB信息（可选）
        
        Returns:
            简洁的设计建议文本
        """
        # V48.12新增：加载完整知识库供 AI 学习
        retriever = get_ggb_retriever()
        
        # 1. 加载所有 GGB 资源知识（完整知识库）
        ggb_knowledge = retriever.load_all_ggb_knowledge()
        
        # 2. 加载所有教学大纲知识（完整知识库）
        syllabus_knowledge = retriever.load_all_syllabus_knowledge()
        
        # 3. 构建完整的背景知识库
        background_info = ""
        if ggb_knowledge:
            background_info += ggb_knowledge
        if syllabus_knowledge:
            background_info += syllabus_knowledge
        if existing_ggb_info:
            background_info += f"\n\n## 用户提供的额外信息\n{existing_ggb_info}\n"
        prompt_template = ChatPromptTemplate.from_template("""
你是一位资深的GeoGebra动态数学软件专家和数学教育专家。

请根据以下信息，为GeoGebra动态图生成简洁实用的设计建议：

## 当前任务
- 章节：{chapter}
- 主题：{topic}
- 教学用途：{teaching_purpose}

{background_info}

## 输出要求

**重要提示**：
- 你已经学习了完整的 GeoGebra 资源知识库和数学教学大纲
- 请基于这些知识，结合当前任务需求，生成创新性的设计建议
- 不要简单复制知识库中的内容，而是要融会贯通、创造性地应用

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
- **步骤要清晰但不过于详细**：提供操作思路和关键功能，但不要给出具体的命令代码（避免AI编造错误命令）
- **重点说明"做什么"和"为什么"**，而不是"怎么点击"
- 突出GeoGebra的动态和交互特性
- 重点关注如何帮助学生理解数学概念
- **基于完整知识库进行创新性设计，而非简单模仿**
- **确保符合教学大纲的核心要求**
- **可以融合多个案例的优点，创造新的设计方案**
- **假设教师具备基本的GeoGebra操作能力**，只需指引方向，无需手把手教学

现在，请生成设计建议。
""")
        
        model = self.model_config.get_model("visualization")
        chain = prompt_template | model | StrOutputParser()
        
        result = chain.invoke({
            "chapter": chapter,
            "topic": topic,
            "teaching_purpose": teaching_purpose,
            "background_info": background_info  # V48.12: 使用背景信息替代 existing_info
        })
        
        return result
    
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应字典
        """
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

---
""",
            "error": error_msg
        }


def generate_ggb_innovation_suggestions(
    chapter: str,
    topic: str,
    teaching_purpose: str,
    existing_ggb_info: Optional[str] = None
) -> Dict[str, Any]:
    """
    生成GGB创新设计建议的适配函数
    
    Args:
        chapter: 章节
        topic: 主题
        teaching_purpose: 教学用途
        existing_ggb_info: 现有GGB信息（可选）
    
    Returns:
        包含设计建议的字典
    """
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
