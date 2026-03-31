from .._shared import *


class _AnalyzeMixin:
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
