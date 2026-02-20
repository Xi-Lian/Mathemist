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

from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


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
        
        existing_info = ""
        if existing_ggb_info:
            existing_info = f"""
## 现有GGB信息
{existing_ggb_info}

请参考现有信息进行补充和完善。
"""
        
        model = self.model_config.get_model("visualization")
        chain = prompt_template | model | StrOutputParser()
        
        result = chain.invoke({
            "chapter": chapter,
            "topic": topic,
            "teaching_purpose": teaching_purpose,
            "existing_info": existing_info
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
