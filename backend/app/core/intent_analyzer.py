"""
意图理解模块

职责：
- 分析用户输入，确定用户意图
- 支持基于LLM的意图识别
- 提供关键词匹配作为备用方案
- V33.0改进：添加数量限制提取、年级信息提取、主题精准识别

依赖：
- model_config (模型配置)
- langchain (提示词和链)

支持的意图类型：
- search: 资源搜索
- generate_lesson_plan: 教案生成
- visualization: 可视化建议
"""

import json
import re
from typing import Dict, Any, List, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .model_config import model_config


class IntentAnalyzer:
    """意图分析器"""
    
    INTENT_SEARCH = "search"
    INTENT_LESSON_PLAN = "generate_lesson_plan"
    INTENT_VISUALIZATION = "visualization"
    
    INSTRUCTION_KEYWORDS = {
        "resource_retrieval": ["推送", "给", "找", "推荐", "有没有", "我要", "帮我找", "想要", "需要"],
        "content_generation": ["生成", "设计", "写", "创作", "帮我做", "制作", "创建", "编写"]
    }
    
    KEYWORDS = {
        INTENT_LESSON_PLAN: [
            "教案", "教学设计", "教学计划", "备课"
        ],
        INTENT_VISUALIZATION: [
            "ggb", "可视化", "动态数学", "几何画板", "图形设计"
        ]
    }
    
    V33_NUMBER_PATTERNS = [
        (r'(\d+)\s*[道个条]', lambda m: int(m.group(1))),
        (r'[给找推荐].*?(\d+)', lambda m: int(m.group(1))),
        (r'(\d+)\s*[题个道]', lambda m: int(m.group(1))),
        (r'几[道个条]', lambda m: 5),
        (r'一些', lambda m: 10),
        (r'一点', lambda m: 5),
        (r'多一点', lambda m: 15),
        (r'很多', lambda m: 20),
    ]
    
    V33_DIFFICULTY_PATTERNS = {
        '基础': ['基础', '简单', '容易', '入门', '初级'],
        '中等': ['中等', '一般', '普通', '适中'],
        '困难': ['困难', '难', '挑战', '拔高', '培优', '提高', '高级'],
        '综合': ['综合', '应用', '实际', '综合应用']
    }
    
    V33_GRADE_PATTERNS = {
        '高一上学期': ['高一上', '高一上学期', '必修一', '必修第一册'],
        '高一下学期': ['高一下', '高一下学期', '必修二', '必修第二册'],
        '高二上学期': ['高二上', '高二上学期', '选择性必修一'],
        '高二下学期': ['高二下', '高二下学期', '选择性必修二'],
        '高三': ['高三', '高考', '选择性必修三', '高三学生', '高考复习', '高考备考', '高三数学', '毕业班'],
        '高一': ['高一', '高中一年级', '高一学生'],
        '高二': ['高二', '高中二年级', '高二学生'],
    }
    
    V33_MATH_TOPIC_CLARIFICATION = {
        "幂函数": {
            "core_keywords": ["幂函数", "y=x^a", "y = x^a", "x的幂", "x的a次方"],
            "exclude_keywords": ["指数运算", "指数幂", "分数指数幂", "根式运算", "8^", "2^", "a^x", "指数函数"],
            "description": "幂函数是形如 y = x^a 的函数，底数是变量x，指数是常数a",
            "focus": "函数性质和图像"
        },
        "指数运算": {
            "core_keywords": ["指数运算", "分数指数幂", "根式运算", "指数幂", "8^(2/3)", "2^(1/2)"],
            "related_keywords": ["8^", "2^", "a^(2/3)", "分数指数", "根式"],
            "description": "指数运算是计算 a^b 形式的值，底数是常数，指数可以是分数",
            "focus": "计算技巧和化简"
        },
        "指数函数": {
            "core_keywords": ["指数函数", "y=a^x", "y=2^x", "y=e^x"],
            "exclude_keywords": ["幂函数", "对数函数"],
            "description": "指数函数是形如 y = a^x 的函数，底数是常数a，指数是变量x",
            "focus": "函数性质和图像"
        },
        "三角恒等变换": {
            "core_keywords": ["三角恒等变换", "三角恒等式", "恒等变换", "和差化积", "积化和差", "二倍角"],
            "related_keywords": ["sin", "cos", "tan", "诱导公式"],
            "description": "三角恒等变换涉及三角函数之间的恒等式变换",
            "focus": "公式变换和化简"
        },
    }
    
    # 上下文意图模式
    CONTEXT_INTENT_PATTERNS = {
        "continue": ["还要", "再来", "继续", "多一点", "再给", "还有"],
        "refine": ["更", "调整", "修改", "换", "重新", "不同"],
        "specific": ["具体", "详细", "详细一点", "具体一点"],
        "difficulty": ["难", "简单", "基础", "中等", "困难", "挑战"],
        "quantity": ["道", "个", "题", "道题", "个题"]
    }
    
    def __init__(self):
        """初始化意图分析器"""
        self.model_config = model_config
        self.prompt_template = self._create_prompt_template()
        self.context_history = []  # 上下文历史
    
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
        
        if not user_input or not user_input.strip():
            print("⚠️ 用户输入为空，使用默认意图")
            return self._get_default_intent("用户输入为空")
        
        try:
            result = self._analyze_with_llm(user_input)
            print(f"✅ LLM意图理解成功")
        except Exception as e:
            print(f"⚠️ LLM意图理解失败: {e}")
            print("🔄 使用关键词匹配作为备用")
            result = self._analyze_with_keywords(user_input)
        
        # 无论使用LLM还是关键词匹配，都使用_extract_resource_types方法来提取资源类型，确保准确性
        extracted_resource_types = self._extract_resource_types(user_input)
        if extracted_resource_types:
            result["resource_types"] = extracted_resource_types
            print(f"📋 提取的资源类型: {extracted_resource_types}")
        
        result["quantity_limit"] = self._extract_quantity_limit(user_input)
        result["grade_info"] = self._extract_grade_info(user_input)
        result["difficulty_info"] = self._extract_difficulty_info(user_input)
        result["clarified_topic"] = self._clarify_math_topic(user_input)
        result["context_analysis"] = self._analyze_context(user_input)
        
        print(f"📋 V33.0数量限制: {result['quantity_limit']}")
        print(f"📋 V33.0年级信息: {result['grade_info']}")
        print(f"📋 V33.0难度信息: {result['difficulty_info']}")
        print(f"📋 V33.0主题澄清: {result['clarified_topic']}")
        print(f"📋 上下文分析: {result['context_analysis']}")
        
        # 更新上下文历史
        self._update_context_history(user_input, result)
        
        return result
    
    def _analyze_context(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入的上下文
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            上下文分析结果
        """
        context_analysis = {
            "context_type": "normal",
            "context_keywords": [],
            "suggestions": []
        }
        
        # 分析上下文类型
        for context_type, keywords in self.CONTEXT_INTENT_PATTERNS.items():
            matched_keywords = [kw for kw in keywords if kw in user_input]
            if matched_keywords:
                context_analysis["context_type"] = context_type
                context_analysis["context_keywords"] = matched_keywords
                
                # 根据上下文类型生成建议
                if context_type == "continue":
                    context_analysis["suggestions"].append("保持当前主题，增加更多资源")
                elif context_type == "refine":
                    context_analysis["suggestions"].append("调整搜索参数，提供更精准的资源")
                elif context_type == "specific":
                    context_analysis["suggestions"].append("提供更详细的资源内容")
                elif context_type == "difficulty":
                    context_analysis["suggestions"].append("根据难度要求筛选资源")
                elif context_type == "quantity":
                    context_analysis["suggestions"].append("根据数量要求限制结果")
                break
        
        # 分析最近上下文
        if self.context_history:
            recent_context = self.context_history[-1]
            if recent_context:
                clarified_topic = recent_context.get("clarified_topic", {})
                if clarified_topic and "主题" in clarified_topic or "resource_types" in recent_context:
                    context_analysis["recent_context"] = recent_context
        
        return context_analysis
    
    def _update_context_history(self, user_input: str, result: Dict[str, Any]) -> None:
        """
        更新上下文历史
        
        Args:
            user_input: 用户输入
            result: 分析结果
        """
        context_entry = {
            "user_input": user_input,
            "intent": result.get("intent"),
            "clarified_topic": result.get("clarified_topic"),
            "resource_types": result.get("resource_types"),
            "timestamp": "2026-03-15"  # 实际应用中应使用当前时间
        }
        
        self.context_history.append(context_entry)
        # 保持历史记录不超过10条
        if len(self.context_history) > 10:
            self.context_history = self.context_history[-10:]
    
    def clear_context(self) -> None:
        """
        清除上下文历史
        """
        self.context_history = []
    
    def _extract_quantity_limit(self, user_input: str) -> Optional[int]:
        """
        V33.0: 从用户输入中提取数量限制
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            数量限制，如果没有则返回None
        """
        for pattern, extractor in self.V33_NUMBER_PATTERNS:
            match = re.search(pattern, user_input)
            if match:
                return extractor(match)
        return None
    
    def _extract_grade_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 从用户输入中提取年级信息
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            年级信息字典
        """
        # V52.0改进：优先匹配更具体的年级（高三、高二、高一），避免误匹配
        # 定义优先级顺序：高三 > 高二 > 高一 > 学期
        priority_order = ['高三', '高二', '高一', '高一上学期', '高一下学期', '高二上学期', '高二下学期']
        
        for grade in priority_order:
            if grade in self.V33_GRADE_PATTERNS:
                keywords = self.V33_GRADE_PATTERNS[grade]
                for keyword in keywords:
                    if keyword in user_input:
                        return {
                            "grade": grade,
                            "grade_keywords_matched": keyword
                        }
        
        return None
    
    def _extract_difficulty_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 从用户输入中提取难度信息
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            难度信息字典
        """
        for difficulty, keywords in self.V33_DIFFICULTY_PATTERNS.items():
            for keyword in keywords:
                if keyword in user_input:
                    return {
                        "difficulty": difficulty,
                        "difficulty_keywords_matched": keyword
                    }
        return None
    
    def _clarify_math_topic(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 澄清数学主题，解决概念混淆问题
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            澄清后的主题信息
        """
        for topic, config in self.V33_MATH_TOPIC_CLARIFICATION.items():
            core_matched = any(kw in user_input for kw in config.get("core_keywords", []))
            exclude_matched = any(kw in user_input for kw in config.get("exclude_keywords", []))
            
            if core_matched:
                return {
                    "topic": topic,
                    "is_confused": exclude_matched,
                    "description": config.get("description", ""),
                    "should_exclude": exclude_matched,
                    "exclude_keywords_matched": [kw for kw in config.get("exclude_keywords", []) if kw in user_input] if exclude_matched else []
                }
        return None
    
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
            cleaned = self._clean_json_response(response)
            parsed = json.loads(cleaned)
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

    def _clean_json_response(self, response: str) -> str:
        """
        清洗模型输出，兼容 Markdown 代码块与前后说明文本。

        Args:
            response: 模型原始响应

        Returns:
            可用于 json.loads 的字符串
        """
        content = (response or "").strip()
        if not content:
            return content

        # 先处理 ```json ... ``` 或 ``` ... ``` 包裹
        fence_match = re.match(
            r"^\s*```(?:json|JSON)?\s*([\s\S]*?)\s*```\s*$",
            content,
        )
        if fence_match:
            content = fence_match.group(1).strip()

        # 若还有前后说明文本，尝试提取最外层 JSON 对象
        first_brace = content.find("{")
        last_brace = content.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            content = content[first_brace:last_brace + 1]

        return content
    
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
        
        # 提取资源类型（V41.0改进：提前提取，用于判断修改意见）
        resource_types = self._extract_resource_types(user_input)
        print(f"📋 提取的资源类型: {resource_types}")
        
        # 检查是否为修改意见
        # V41.0改进：区分"想要/需要"表示资源获取还是修改意见
        # 如果用户输入包含资源获取指令词和资源类型，则优先识别为资源获取
        revision_keywords_strict = [
            # 表达不满意
            "觉得", "感觉", "认为", "希望", "应该", "建议", "提议",
            # 具体修改动作
            "修改", "调整", "改进", "完善", "优化", "补充", "增加", "添加", "减少", "删除", "删除掉",
            # 疑问式修改请求
            "能不能", "能否", "可不可以", "是否可以", "能不能够",
            # 具体修改内容
            "太短", "太长", "太简单", "太复杂", "不够", "不足", "缺少", "缺乏",
            # 其他修改相关词汇
            "改一下", "改改", "调整一下", "完善一下", "优化一下", "补充一下"
        ]
        # "想要"和"需要"单独判断，因为它们既可能是资源获取也可能是修改意见
        want_need_keywords = ["想要", "需要"]
        has_want_need = any(keyword in user_input for keyword in want_need_keywords)
        has_revision_request_strict = any(keyword in user_input for keyword in revision_keywords_strict)
        
        # V41.0改进：如果包含"想要/需要"但不包含严格修改关键词，且包含资源类型，则识别为资源获取
        if has_want_need and not has_revision_request_strict:
            # 检查是否包含资源类型
            if resource_types and any(rt in ["习题", "题目", "练习", "教案", "课件", "课例", "GGB", "资料"] for rt in resource_types):
                print("🎯 V41.0：'想要/需要' + 资源类型，识别为资源获取意图")
                has_revision_request = False
            else:
                # 没有明确的资源类型，可能是修改意见
                has_revision_request = True
        else:
            has_revision_request = has_revision_request_strict or (has_want_need and has_revision_request_strict)
        
        print(f"📋 包含修改意见关键词: {has_revision_request}")
        
        print(f"📋 包含教案关键词: {has_lesson_plan}")
        print(f"📋 包含可视化关键词: {has_visualization}")
        
        # 生成用户需求描述
        user_needs = self._generate_user_needs(user_input, resource_types)
        print(f"📋 生成的用户需求: {user_needs}")
        
        # 确定意图
        # 优先级：修改意见 > 内容生成+教案 > 内容生成 > 资源获取+教案 > 资源获取 > 关键词
        if has_revision_request:
            # 修改意见请求，使用generate_lesson_plan意图
            print("🎯 识别到修改意见，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到修改意见",
                user_needs,
                resource_types
            )
        elif has_content_generation and has_lesson_plan:
            print("🎯 识别到内容生成指令词和教案关键词，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到内容生成指令词和教案关键词",
                user_needs,
                resource_types
            )
        elif has_content_generation:
            print("🎯 识别到内容生成指令词，使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "识别到内容生成指令词",
                user_needs,
                resource_types
            )
        elif has_resource_retrieval:
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
        # V52.0改进：添加"例子"作为习题类型，因为用户说"例子"时通常是指习题例子
        type_keywords = {
            "资料": ["资料", "资源"],
            "习题": ["习题", "题目", "练习", "练习题", "测试", "测试题", "作业", "试题", "考题", "填空题", "选择题", "解答题", "计算题", "证明题", "应用题", "作图题", "例子", "实例", "案例"],
            "教案": ["教案", "教学设计", "备课", "教学计划"],
            "课件": ["课件", "PPT", "幻灯片"],
            "课例": ["课例", "教学案例", "视频课", "课堂实录"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示"],
            "教学大纲": ["教学大纲", "课程标准", "教学要求"]
        }
        
        # 对于中文输入，不需要转换为小写，直接使用原始输入
        # 对于英文输入，转换为小写以确保匹配
        user_input_processed = user_input.lower() if any(c.isalpha() for c in user_input) else user_input
        
        # 检查每种资源类型
        for resource_type, keywords in type_keywords.items():
            if any(keyword in user_input_processed for keyword in keywords):
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
