"""
可视化建议模块

职责：
- 根据用户需求和检索到的示例生成可视化设计建议
- 提供专业的GGB动态数学设计指导
- 整合优秀设计示例

依赖：
- model_config (模型配置)
- langchain (提示词和链)
"""

from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


class VisualizationAdvisor:
    """可视化建议器"""
    
    def __init__(self):
        """初始化可视化建议器"""
        self.model_config = model_config
        self.prompt_template = self._create_prompt_template()
    
    def advise(
        self, 
        user_input: str, 
        visualization_examples: List[Dict[str, Any]]
    ) -> str:
        """
        生成可视化设计建议
        
        Args:
            user_input: 用户需求
            visualization_examples: 可视化示例列表
        
        Returns:
            可视化建议文本
        """
        print(f"\n====================================")
        print(f"🎨 可视化建议生成开始")
        print(f"📝 用户需求: {user_input}")
        print(f"📊 可视化示例: {len(visualization_examples)}条")
        
        try:
            # 准备输入数据
            examples_text = self._format_visualization_examples(visualization_examples)
            
            # 获取模型
            model = self.model_config.get_model("visualization")
            
            # 构建链
            chain = self.prompt_template | model | StrOutputParser()
            
            # 调用模型生成建议
            suggestions = chain.invoke({
                "user_input": user_input,
                "visualization_examples": examples_text
            })
            
            print(f"✅ 可视化建议生成成功，长度: {len(suggestions)}字符")
            
            return suggestions
            
        except Exception as e:
            print(f"❌ 可视化建议生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
    def _format_visualization_examples(self, examples: List[Dict[str, Any]]) -> str:
        """
        格式化可视化示例
        
        Args:
            examples: 可视化示例列表
        
        Returns:
            格式化后的文本
        """
        if not examples:
            return "暂无优秀可视化设计示例"
        
        formatted = []
        for i, example in enumerate(examples, 1):
            title = example.get("title", f"示例{i}")
            content = example.get("content", "")
            
            # 截取内容（避免过长）
            if len(content) > 500:
                content = content[:500] + "..."
            
            formatted.append(f"优秀设计示例{i}：{title}\n{content}")
        
        return "\n\n".join(formatted)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"抱歉，可视化建议生成过程中出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建可视化建议的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一个专业的GGB动态数学设计专家。

请根据用户需求和检索到的优秀设计示例，提供专业的GGB动态数学设计建议。

用户需求：{user_input}

检索到的优秀设计示例：
{visualization_examples}

可视化设计建议要求：
1. 设计核心思想
2. GGB构建步骤
3. 交互性设计
4. 教学应用场景
5. 预期教学效果
6. 参考检索到的优秀设计示例进行泛化

请提供专业、详细且可操作的可视化设计建议。
""")


# 向后兼容的函数接口
def visualization_suggestions_node(state) -> Dict[str, Any]:
    """
    可视化建议节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含可视化建议的更新状态
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 提取检索到的资源
    visualization_examples = []
    
    if isinstance(state, dict):
        retrieved_resources = state.get('retrieved_resources', {})
        visualization_examples = retrieved_resources.get('visualization_examples', [])
    
    # 生成可视化建议
    advisor = VisualizationAdvisor()
    suggestions = advisor.advise(user_input, visualization_examples)
    
    return {
        "visualization_suggestions": suggestions,
        "current_step": "visualization_suggestions",
        "error": None
    }
