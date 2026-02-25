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
    
    # 指令词配置
    INSTRUCTION_KEYWORDS = {
        "resource_retrieval": ["推送", "给", "找", "推荐", "有没有", "我要", "帮我找", "想要", "需要"],
        "content_generation": ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
    }
    
    # 关键词配置
    KEYWORDS = {
        INTENT_LESSON_PLAN: [
            "教案", "教学设计", "教学计划", "备课"
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
            user_needs = parsed.get("user_needs", "")
            resource_types = parsed.get("resource_types", [])
            
            # 验证intents格式
            if not isinstance(intents, list):
                intents = [{"type": self.INTENT_SEARCH, "confidence": 1.0}]
            
            print(f"📋 主要意图: {primary_intent}")
            print(f"📋 用户需求: {user_needs}")
            print(f"📋 资源类型: {resource_types}")
            print(f"📋 所有意图: {intents}")
            
            return {
                "intent": primary_intent,
                "user_needs": user_needs,
                "resource_types": resource_types,
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
        
        # 检查指令词
        has_resource_retrieval = any(keyword in user_input for keyword in self.INSTRUCTION_KEYWORDS["resource_retrieval"])
        has_content_generation = any(keyword in user_input for keyword in self.INSTRUCTION_KEYWORDS["content_generation"])
        
        print(f"📋 包含资源获取指令词: {has_resource_retrieval}")
        print(f"📋 包含内容生成指令词: {has_content_generation}")
        
        # 检查关键词
        has_lesson_plan = self._has_keywords(user_input_lower, self.INTENT_LESSON_PLAN)
        has_visualization = self._has_keywords(user_input_lower, self.INTENT_VISUALIZATION)
        
        print(f"📋 包含教案关键词: {has_lesson_plan}")
        print(f"📋 包含可视化关键词: {has_visualization}")
        
        # 提取资源类型
        resource_types = self._extract_resource_types(user_input)
        print(f"📋 提取的资源类型: {resource_types}")
        
        # 生成用户需求描述
        user_needs = self._generate_user_needs(user_input, resource_types)
        print(f"📋 生成的用户需求: {user_needs}")
        
        # 确定意图
        # 优先级：内容生成+教案 > 内容生成 > 资源获取+教案 > 资源获取 > 关键词
        if has_content_generation and has_lesson_plan:
            # 同时有内容生成指令词和教案关键词，优先识别为教案生成
            print("🎯 识别到内容生成指令词和教案关键词，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到内容生成指令词和教案关键词",
                user_needs,
                resource_types
            )
        elif has_content_generation:
            # 内容生成指令词，使用generate_lesson_plan意图
            print("🎯 识别到内容生成指令词，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到内容生成指令词",
                user_needs,
                resource_types
            )
        elif has_resource_retrieval and has_lesson_plan:
            # 资源获取指令词+教案关键词，优先识别为教案生成（用户可能想要教案示例）
            print("🎯 识别到资源获取指令词和教案关键词，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到资源获取指令词和教案关键词",
                user_needs,
                resource_types
            )
        elif has_resource_retrieval:
            # 资源获取指令词，使用search意图
            print("🎯 识别到资源获取指令词，使用search意图")
            return self._get_single_intent_result(
                self.INTENT_SEARCH,
                "识别到资源获取指令词",
                user_needs,
                resource_types
            )
        elif has_lesson_plan and has_visualization:
            return self._get_multi_intent_result(
                self.INTENT_LESSON_PLAN,
                self.INTENT_VISUALIZATION,
                "模型返回格式错误，使用关键词匹配",
                user_needs,
                resource_types
            )
        elif has_lesson_plan:
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "模型返回格式错误，使用关键词匹配",
                user_needs,
                resource_types
            )
        elif has_visualization:
            return self._get_single_intent_result(
                self.INTENT_VISUALIZATION,
                "模型返回格式错误，使用关键词匹配",
                user_needs,
                resource_types
            )
        else:
            print("⚠️ 没有匹配关键词，使用默认意图")
            return self._get_default_intent("没有匹配关键词", user_needs, resource_types)
    
    def _extract_resource_types(self, user_input: str) -> List[str]:
        """
        从用户输入中提取资源类型
        
        Args:
            user_input: 用户输入
        
        Returns:
            资源类型列表
        """
        resource_types = []
        
        # 资源类型关键词映射
        type_keywords = {
            "资料": ["资料", "资源"],
            "习题": ["习题", "题目", "练习", "测试", "作业"],
            "教案": ["教案", "教学设计", "备课", "教学计划"],
            "课件": ["课件", "PPT", "幻灯片"],
            "课例": ["课例", "教学案例", "视频课", "课堂实录"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示"],
            "教学大纲": ["教学大纲", "课程标准", "教学要求"]
        }
        
        user_input_lower = user_input.lower()
        
        # 检查每种资源类型
        for resource_type, keywords in type_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                resource_types.append(resource_type)
        
        return resource_types
    
    def _generate_user_needs(self, user_input: str, resource_types: List[str]) -> str:
        """
        生成用户需求描述
        
        Args:
            user_input: 用户输入
            resource_types: 资源类型列表
        
        Returns:
            用户需求描述
        """
        if resource_types:
            return f"用户想要查找{', '.join(resource_types)}相关的资源"
        else:
            return "用户想要查找相关的教学资源"
    
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
        error_msg: str = None,
        user_needs: str = "",
        resource_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取单一意图结果
        
        Args:
            primary_intent: 主要意图
            error_msg: 错误信息
            user_needs: 用户需求描述
            resource_types: 资源类型列表
        
        Returns:
            意图结果
        """
        if resource_types is None:
            resource_types = []
        
        return {
            "intent": primary_intent,
            "user_needs": user_needs,
            "resource_types": resource_types,
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
        error_msg: str = None,
        user_needs: str = "",
        resource_types: List[str] = None
    ) -> Dict[str, Any]:
        """
        获取多意图结果
        
        Args:
            primary_intent: 主要意图
            secondary_intent: 次要意图
            error_msg: 错误信息
            user_needs: 用户需求描述
            resource_types: 资源类型列表
        
        Returns:
            意图结果
        """
        if resource_types is None:
            resource_types = []
        
        return {
            "intent": primary_intent,
            "user_needs": user_needs,
            "resource_types": resource_types,
            "intents": [
                {"type": primary_intent, "confidence": 0.9},
                {"type": secondary_intent, "confidence": 0.8},
                {"type": self.INTENT_SEARCH, "confidence": 0.1}
            ],
            "current_step": "intent_understanding",
            "error": error_msg
        }
    
    def _get_default_intent(self, error_msg: str = None, user_needs: str = "", resource_types: List[str] = None) -> Dict[str, Any]:
        """
        获取默认意图结果
        
        Args:
            error_msg: 错误信息
            user_needs: 用户需求描述
            resource_types: 资源类型列表
        
        Returns:
            意图结果
        """
        if resource_types is None:
            resource_types = []
        
        return {
            "intent": self.INTENT_SEARCH,
            "user_needs": user_needs,
            "resource_types": resource_types,
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
   - 例如："生成指数函数的教案"、"帮我设计三角函数的教学"

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

## 特殊说明

- 当用户说"资料"或"资源"时，表示用户想要所有类型的教学资源（习题、教案、课件、GGB、教学大纲等）
- 当用户明确指定某种资源类型时（如"习题"、"教案"），只返回该类型
- 不要过度推断用户需求，只输出用户明确提到的资源类型

用户输入：{user_input}

请根据以上要求，输出JSON格式的分析结果。
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
