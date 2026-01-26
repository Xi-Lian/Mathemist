import os
import json
from typing import Dict, Any, Optional, List
import requests
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_deepseek import ChatDeepSeek
from .state import MathAgentState

# DeepSeek API配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "your-api-key-here")
DEEPSEEK_MODEL = "deepseek-chat"

# 初始化DeepSeek模型
deepseek_llm = ChatDeepSeek(
    model=DEEPSEEK_MODEL,
    api_key=DEEPSEEK_API_KEY,
    temperature=0.3,
    max_tokens=2000
)

# 模型选择函数
def get_model(task_type: str = "default"):
    """
    根据任务类型选择合适的模型
    
    Args:
        task_type: 任务类型，可选值：intent（意图理解）、lesson_plan（教案生成）、visualization（可视化建议）
    
    Returns:
        选择的语言模型
    """
    # 统一使用DeepSeek模型
    return deepseek_llm

# 意图理解提示词
intent_prompt = ChatPromptTemplate.from_template("""
你是一个高中数学教育智能助手的意图理解模块。

请分析用户的输入，判断用户的意图类型：
1. search: 用户想要搜索数学资源、习题、知识点等
2. generate_lesson_plan: 用户想要生成教案、教学设计
3. visualization: 用户想要获取可视化设计建议、GGB动态数学设计

用户输入：{user_input}

请仅输出一个单词，表示意图类型：search、generate_lesson_plan或visualization
""")

# 教案生成提示词
lesson_plan_prompt = ChatPromptTemplate.from_template("""
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
6. 符合高中学数学教学大纲要求
7. 参考优秀教案的共性特征

请生成一个结构清晰、内容详实的教案。
""")

# 可视化设计建议提示词
visualization_prompt = ChatPromptTemplate.from_template("""
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

# 资源检索函数（暂时返回空结果，等待数据库搭建完成）
def retrieve_resources(query: str, intent: str) -> Dict[str, Any]:
    """
    根据查询和意图检索相关资源
    当前版本暂时返回空结果，等待ChromaDB搭建完成后再实现
    
    Args:
        query: 用户查询
        intent: 用户意图
    
    Returns:
        检索结果字典，包含理论依据、教案共性、可视化示例等
    """
    # 暂时返回空结果，等待数据库搭建完成
    return {
        "theory_resources": [],  # 教育理论资源
        "lesson_plan_patterns": [],  # 优秀教案共性
        "visualization_examples": [],  # 可视化设计示例
        "general_resources": []  # 通用资源
    }

# 意图理解节点
def intent_understanding_node(state: MathAgentState) -> Dict[str, Any]:
    """
    意图理解节点
    分析用户输入，确定用户意图
    """
    try:
        # 使用DeepSeek模型进行意图理解
        model = get_model("intent")
        print(f"意图理解使用的模型: {type(model).__name__}")
        
        intent_chain = intent_prompt | model | StrOutputParser()
        intent = intent_chain.invoke({"user_input": state.user_input})
        
        print(f"识别到的意图: {intent}")
        
        # 标准化意图输出
        intent = intent.strip().lower()
        if intent not in ["search", "generate_lesson_plan", "visualization"]:
            intent = "search"  # 默认意图
        
        return {
            "intent": intent,
            "current_step": "intent_understanding",
            "error": None
        }
    except Exception as e:
        return {
            "intent": "search",  # 默认意图
            "current_step": "intent_understanding",
            "error": f"意图理解失败: {str(e)}"
        }

# 资源检索节点
def resource_retrieval_node(state: MathAgentState) -> Dict[str, Any]:
    """
    资源检索节点
    根据用户意图和输入检索相关资源
    """
    try:
        print(f"开始资源检索，意图: {state.intent}")
        
        # 调用资源检索函数
        retrieved_resources = retrieve_resources(
            query=state.user_input,
            intent=state.intent
        )
        
        print(f"检索到 {len(retrieved_resources.get('theory_resources', []))} 条理论资源")
        print(f"检索到 {len(retrieved_resources.get('lesson_plan_patterns', []))} 条教案共性")
        print(f"检索到 {len(retrieved_resources.get('visualization_examples', []))} 条可视化示例")
        
        return {
            "retrieved_resources": retrieved_resources,
            "current_step": "resource_retrieval",
            "error": None
        }
    except Exception as e:
        return {
            "retrieved_resources": {
                "theory_resources": [],
                "lesson_plan_patterns": [],
                "visualization_examples": [],
                "general_resources": []
            },
            "current_step": "resource_retrieval",
            "error": f"资源检索失败: {str(e)}"
        }

# 教案生成节点
def lesson_plan_generation_node(state: MathAgentState) -> Dict[str, Any]:
    """
    教案生成节点
    根据用户需求和检索到的理论依据、优秀教案共性生成教案
    """
    try:
        # 准备理论依据文本
        theory_text = "\n".join([
            f"- {r.get('title', '理论')}: {r.get('content', '')}"
            for r in state.retrieved_resources.get("theory_resources", [])
        ])
        
        # 准备教案共性文本
        patterns_text = "\n".join([
            f"- {r.get('title', '共性')}: {r.get('content', '')}"
            for r in state.retrieved_resources.get("lesson_plan_patterns", [])
        ])
        
        # 使用DeepSeek模型生成教案
        model = get_model("lesson_plan")
        print(f"教案生成使用的模型: {type(model).__name__}")
        
        lesson_plan_chain = lesson_plan_prompt | model | StrOutputParser()
        lesson_plan = lesson_plan_chain.invoke({
            "user_input": state.user_input,
            "theory_resources": theory_text if theory_text else "暂无相关理论依据",
            "lesson_plan_patterns": patterns_text if patterns_text else "暂无优秀教案共性"
        })
        
        print(f"教案生成完成，长度: {len(lesson_plan)} 字符")
        
        return {
            "lesson_plan": lesson_plan,
            "current_step": "lesson_plan_generation",
            "error": None
        }
    except Exception as e:
        return {
            "lesson_plan": None,
            "current_step": "lesson_plan_generation",
            "error": f"教案生成失败: {str(e)}"
        }

# 可视化设计建议节点
def visualization_suggestion_node(state: MathAgentState) -> Dict[str, Any]:
    """
    可视化设计建议节点
    为用户提供GGB动态数学设计建议，基于检索到的可视化设计示例
    """
    try:
        # 准备可视化示例文本
        examples_text = "\n".join([
            f"- {r.get('title', '示例')}: {r.get('content', '')}"
            for r in state.retrieved_resources.get("visualization_examples", [])
        ])
        
        # 使用DeepSeek模型生成可视化设计建议
        visualization_chain = visualization_prompt | get_model("visualization") | StrOutputParser()
        visualization_suggestions = visualization_chain.invoke({
            "user_input": state.user_input,
            "visualization_examples": examples_text if examples_text else "暂无相关设计示例"
        })
        
        return {
            "visualization_suggestions": visualization_suggestions,
            "current_step": "visualization_suggestion",
            "error": None
        }
    except Exception as e:
        return {
            "visualization_suggestions": None,
            "current_step": "visualization_suggestion",
            "error": f"可视化设计建议生成失败: {str(e)}"
        }

# 搜索结果处理节点
def search_result_processing_node(state: MathAgentState) -> Dict[str, Any]:
    """
    搜索结果处理节点
    格式化搜索结果并返回给用户
    当前版本暂时返回提示信息，等待数据库搭建完成后再实现
    """
    try:
        # 暂时返回提示信息
        search_results = "知识库正在建设中，资源检索功能将在数据库搭建完成后启用。"
        
        return {
            "search_results": search_results,
            "current_step": "search_result_processing",
            "error": None
        }
    except Exception as e:
        return {
            "search_results": "搜索结果处理失败",
            "current_step": "search_result_processing",
            "error": f"搜索结果处理失败: {str(e)}"
        }

# 响应格式化节点
def response_formatting_node(state: MathAgentState) -> Dict[str, Any]:
    """
    响应格式化节点
    根据不同的意图和执行结果，格式化最终响应
    """
    try:
        # 根据意图生成不同的响应
        if state.intent == "search":
            response = state.search_results if state.search_results else "搜索功能正在建设中"
        elif state.intent == "generate_lesson_plan":
            response = state.lesson_plan if state.lesson_plan else "教案生成失败"
        elif state.intent == "visualization":
            response = state.visualization_suggestions if state.visualization_suggestions else "可视化建议生成失败"
        else:
            response = "未知的意图类型"
        
        return {
            "response": response,
            "current_step": "response_formatting",
            "error": None
        }
    except Exception as e:
        return {
            "response": "响应格式化失败",
            "current_step": "response_formatting",
            "error": f"响应格式化失败: {str(e)}"
        }
