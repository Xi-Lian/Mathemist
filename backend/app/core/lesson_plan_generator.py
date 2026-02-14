"""
教案生成模块

职责：
- 根据用户需求和检索到的资源生成教案
- 整合理论依据和优秀教案特征
- 提供结构化的教案输出

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
        格式化理论资源
        
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
            
            # 截取内容（避免过长）
            if len(content) > 800:
                content = content[:800] + "..."
            
            formatted.append(f"理论卡片{i}：{title}\n来源：{source}\n内容：{content}\n")
        
        return "\n\n".join(formatted)
    
    def _format_lesson_plan_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """
        格式化教案示例
        
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
            
            # 截取内容（避免过长）
            if len(content) > 500:
                content = content[:500] + "..."
            
            formatted.append(f"优秀教案{i}：{title}\n{content}")
        
        return "\n\n".join(formatted)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"抱歉，教案生成过程中出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建教案生成的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一个专业的高中数学教学设计专家。

请根据用户需求、检索到的理论依据和优秀教案共性，生成一个完整的高中数学教案。

用户需求：{user_input}

检索到的教育理论：
{theory_resources}

优秀教案的共性特征：
{lesson_plan_patterns}

教案要求：
1. 包含教学目标、教学重难点、教学方法
2. 包含详细的教学过程（引入、探究、应用、总结）
3. 包含师生活动设计
4. 包含GGB动态数学设计应用点
5. 提供理论依据支持（基于检索到的教育理论）
6. 符合高中数学教学大纲要求
7. 参考优秀教案的共性特征

**重要要求 - 理论依据引用：**
8. 在教案的每个相关环节，明确标注使用了哪些理论依据，格式为[理论卡片X：理论名称]，例如[理论卡片1：建构主义学习理论]
9. 理论依据引用应该具体、有针对性，不能泛泛而谈
10. 在教案结尾处，添加一个"理论依据使用总结"部分，列出本教案使用的所有理论依据及其应用场景
11. 理论依据的使用应该体现"依据理论，有理论可依"的亮点，展示教案设计的科学性和专业性

**理论依据引用示例：**
- 在教学目标设计环节：[理论卡片1：布鲁姆教育目标分类学]
- 在教学重难点分析环节：[理论卡片2：最近发展区理论]
- 在教学过程设计环节：[理论卡片3：建构主义学习理论]
- 在师生活动设计环节：[理论卡片4：合作学习理论]

请生成一个结构清晰、内容详实、理论依据充分的教案，突出"依据理论，有理论可依"的特色。
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
