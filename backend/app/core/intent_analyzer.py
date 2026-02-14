"""
意图理解模块

职责：
- 分析用户输入，确定用户意图
- 支持基于LLM的意图识别
- 提供关键词匹配作为备用方案

依赖：
- model_config (模型配置)
- langchain (提示词和链)

支持的意图类型：
- search: 资源搜索
- generate_lesson_plan: 教案生成
- visualization: 可视化建议
"""

import json
from typing import Dict, Any, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


class IntentAnalyzer:
    """意图分析器"""
    
    # 意图类型
    INTENT_SEARCH = "search"
    INTENT_LESSON_PLAN = "generate_lesson_plan"
    INTENT_VISUALIZATION = "visualization"
    
    # 关键词配置
    KEYWORDS = {
        INTENT_LESSON_PLAN: [
            "教案", "教学设计", "生成教案", "教学计划", "备课"
        ],
        INTENT_VISUALIZATION: [
            "ggb", "可视化", "动态数学", "几何画板", "图形设计"
        ]
    }
    
    def __init__(self):
        """初始化意图分析器"""
        self.model_config = model_config
        self.prompt_template = self._create_prompt_template()
    
    def analyze(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入，确定意图
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            意图分析结果，包含primary_intent和intents
        """
        print(f"\n====================================")
        print(f"🔍 意图理解开始")
        print(f"📝 用户输入: {user_input}")
        
        # 检查输入是否为空
        if not user_input or not user_input.strip():
            print("⚠️ 用户输入为空，使用默认意图")
            return self._get_default_intent("用户输入为空")
        
        # 尝试使用LLM进行意图理解
        try:
            result = self._analyze_with_llm(user_input)
            print(f"✅ LLM意图理解成功")
            return result
        except Exception as e:
            print(f"⚠️ LLM意图理解失败: {e}")
            print("🔄 使用关键词匹配作为备用")
            return self._analyze_with_keywords(user_input)
    
    def _analyze_with_llm(self, user_input: str) -> Dict[str, Any]:
        """
        使用LLM进行意图理解
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图分析结果
        """
        print("🤖 调用DeepSeek模型进行意图理解...")
        
        # 获取模型
        model = self.model_config.get_model("intent")
        
        # 构建链
        chain = self.prompt_template | model | StrOutputParser()
        
        # 调用模型
        model_response = chain.invoke({"user_input": user_input})
        
        print(f"🤖 模型响应: {model_response}")
        
        # 解析模型响应
        return self._parse_llm_response(model_response)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: 模型响应文本
        
        Returns:
            解析后的意图结果
        """
        try:
            parsed = json.loads(response)
            primary_intent = parsed.get("primary_intent", self.INTENT_SEARCH)
            intents = parsed.get("intents", [])
            
            # 验证intents格式
            if not isinstance(intents, list):
                intents = [{"type": self.INTENT_SEARCH, "confidence": 1.0}]
            
            print(f"📋 主要意图: {primary_intent}")
            print(f"📋 所有意图: {intents}")
            
            return {
                "intent": primary_intent,
                "intents": intents,
                "current_step": "intent_understanding",
                "error": None
            }
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            raise
    
    def _analyze_with_keywords(self, user_input: str) -> Dict[str, Any]:
        """
        使用关键词匹配进行意图理解
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图分析结果
        """
        user_input_lower = user_input.lower()
        
        # 检查关键词
        has_lesson_plan = self._has_keywords(user_input_lower, self.INTENT_LESSON_PLAN)
        has_visualization = self._has_keywords(user_input_lower, self.INTENT_VISUALIZATION)
        
        print(f"📋 包含教案关键词: {has_lesson_plan}")
        print(f"📋 包含可视化关键词: {has_visualization}")
        
        # 确定意图
        if has_lesson_plan and has_visualization:
            return self._get_multi_intent_result(
                self.INTENT_LESSON_PLAN,
                self.INTENT_VISUALIZATION,
                "模型返回格式错误，使用关键词匹配"
            )
        elif has_lesson_plan:
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "模型返回格式错误，使用关键词匹配"
            )
        elif has_visualization:
            return self._get_single_intent_result(
                self.INTENT_VISUALIZATION,
                "模型返回格式错误，使用关键词匹配"
            )
        else:
            print("⚠️ 没有匹配关键词，使用默认意图")
            return self._get_default_intent("没有匹配关键词")
    
    def _has_keywords(self, text: str, intent_type: str) -> bool:
        """
        检查文本是否包含指定意图的关键词
        
        Args:
            text: 输入文本
            intent_type: 意图类型
        
        Returns:
            是否包含关键词
        """
        keywords = self.KEYWORDS.get(intent_type, [])
        return any(keyword in text for keyword in keywords)
    
    def _get_single_intent_result(
        self, 
        primary_intent: str, 
        error_msg: str = None
    ) -> Dict[str, Any]:
        """
        获取单一意图结果
        
        Args:
            primary_intent: 主要意图
            error_msg: 错误信息
        
        Returns:
            意图结果
        """
        return {
            "intent": primary_intent,
            "intents": [
                {"type": primary_intent, "confidence": 0.9},
                {"type": self.INTENT_SEARCH, "confidence": 0.1},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
    
    def _get_multi_intent_result(
        self, 
        primary_intent: str, 
        secondary_intent: str,
        error_msg: str = None
    ) -> Dict[str, Any]:
        """
        获取多意图结果
        
        Args:
            primary_intent: 主要意图
            secondary_intent: 次要意图
            error_msg: 错误信息
        
        Returns:
            意图结果
        """
        return {
            "intent": primary_intent,
            "intents": [
                {"type": primary_intent, "confidence": 0.9},
                {"type": secondary_intent, "confidence": 0.8},
                {"type": self.INTENT_SEARCH, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
    
    def _get_default_intent(self, error_msg: str = None) -> Dict[str, Any]:
        """
        获取默认意图结果
        
        Args:
            error_msg: 错误信息
        
        Returns:
            意图结果
        """
        return {
            "intent": self.INTENT_SEARCH,
            "intents": [
                {"type": self.INTENT_SEARCH, "confidence": 0.9},
                {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
    
    def _create_prompt_template(self) -> ChatPromptTemplate:
        """
        创建意图理解的提示词模板
        
        Returns:
            ChatPromptTemplate实例
        """
        return ChatPromptTemplate.from_template("""
你是一个高中数学教育智能助手的意图理解模块。

请分析用户的输入，判断用户可能的意图类型和置信度。
可能的意图类型包括：
1. search: 用户想要搜索数学资源、习题、知识点等
2. generate_lesson_plan: 用户想要生成教案、教学设计，或者查找教案资源
3. visualization: 用户想要获取可视化设计建议、GGB动态数学设计

用户输入：{user_input}

请输出一个JSON对象，包含以下字段：
- primary_intent: 主要意图
- intents: 一个数组，包含所有可能的意图及其置信度，格式为[{{"type": "意图类型", "confidence": 置信度}}]

示例输出：
{{"primary_intent": "generate_lesson_plan", "intents": [{{"type": "generate_lesson_plan", "confidence": 0.9}}, {{"type": "visualization", "confidence": 0.8}}, {{"type": "search", "confidence": 0.1}}]}}
""")


# 向后兼容的函数接口
def intent_understanding_node(state) -> Dict[str, Any]:
    """
    意图理解节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        意图分析结果
    """
    # 提取用户输入
    user_input = ""
    if hasattr(state, 'user_input'):
        user_input = getattr(state, 'user_input', '')
    elif isinstance(state, dict):
        user_input = state.get('user_input', '')
    
    # 确保是字符串
    user_input = str(user_input) if user_input else ''
    
    # 分析意图
    analyzer = IntentAnalyzer()
    return analyzer.analyze(user_input)
