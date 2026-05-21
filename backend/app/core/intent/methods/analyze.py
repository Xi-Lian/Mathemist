from .._shared import *


class _AnalyzeMixin:
    def _normalize_text(self, user_input: str) -> str:
        return re.sub(r"\s+", "", str(user_input or ""))

    def _build_conversation_result(
        self,
        user_input: str,
        confidence: float = 0.92,
        user_needs: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "intent": self.INTENT_CONVERSATION,
            "user_needs": user_needs or f"用户希望先通过对话确认需求：{user_input}",
            "resource_types": [],
            "intents": [
                {"type": self.INTENT_CONVERSATION, "confidence": confidence},
                {"type": self.INTENT_SEARCH, "confidence": 0.2},
                {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.1},
            ],
            "current_step": "intent_understanding",
            "error": None,
            "skip_retrieval": True,
        }

    def _should_clarify_before_search(self, user_input: str, resource_types: Optional[List[str]]) -> bool:
        normalized = self._normalize_text(user_input)
        if not normalized or resource_types:
            return False

        if self._has_strong_generation_signal(normalized):
            return False

        if self._has_explicit_search_signal(normalized):
            return False

        if any(keyword in normalized for keyword in ["ggb", "geogebra", "可视化", "动态图"]):
            return False

        # 保守方案：如果上一个回复是追问，而用户的回复中包含资源类型词，直接执行检索
        # 这样用户在回答追问时，如果提供了资源类型，就能直接进入搜索流程
        if self.context_history and len(self.context_history) >= 2:
            last_ai_message = None
            for item in reversed(self.context_history):
                if item.get("role") == "assistant" or item.get("type") == "ai":
                    last_ai_message = item.get("content", "") or ""
                    break

            if last_ai_message:
                # 检查上一条AI消息是否是追问（包含问号且较短）
                question_markers = ["？", "?", "请确认", "请告诉我", "请选择"]
                is_question = any(marker in last_ai_message for marker in question_markers) and len(last_ai_message) < 200

                # 如果上一条是追问，且当前回复包含资源类型词，不追问
                if is_question:
                    extracted_types = self._extract_resource_types(user_input)
                    if extracted_types:
                        print("[搜索] 保守方案：检测到用户在回答追问，且包含资源类型词，跳过追问直接搜索")
                        return False

        # 只给一个主题词时，先确认需求，而不是直接冲搜索链路。
        return len(normalized) <= 12

    def _has_strong_generation_signal(self, user_input: str) -> bool:
        normalized = self._normalize_text(user_input)
        generation_patterns = [
            "生成",
            "设计",
            "编写",
            "制作",
            "创建",
            "输出",
            "整理成教案",
            "写一份",
            "写个",
            "写一个",
            "做一份",
            "做个",
            "做一个",
            "帮我做",
        ]
        return any(pattern in normalized for pattern in generation_patterns)

    def _has_explicit_search_signal(self, user_input: str) -> bool:
        normalized = self._normalize_text(user_input)
        search_patterns = [
            "搜",
            "搜索",
            "查",
            "查找",
            "检索",
            "找",
            "推荐",
            "有没有",
            "给我",
            "帮我找",
            "帮我搜",
            "来点",
            "来几个",
            "来一些",
        ]
        return any(pattern in normalized for pattern in search_patterns)

    def _should_prefer_search_for_resource_request(self, user_input: str, resource_types: Optional[List[str]]) -> bool:
        if not resource_types:
            return False

        normalized = self._normalize_text(user_input)
        if not normalized:
            return False

        if self._has_strong_generation_signal(normalized):
            return False

        if self._has_explicit_search_signal(normalized):
            return True

        # 像“对数教案”“二次函数习题”这种短语，默认理解为找现成资源而不是让系统生成。
        return len(normalized) <= 16

    def _apply_intent_overrides(self, user_input: str, result: Dict[str, Any]) -> Dict[str, Any]:
        resource_types = result.get("resource_types") or []
        if self._should_clarify_before_search(user_input, resource_types):
            return self._build_conversation_result(
                user_input,
                confidence=0.9,
                user_needs=f"用户只给出了主题“{self._normalize_text(user_input) or user_input}”，需要先通过对话澄清是搜资源、生成教案还是做可视化",
            )

        if self._should_prefer_search_for_resource_request(user_input, resource_types):
            if result.get("intent") != self.INTENT_SEARCH:
                print("🛠️ 意图纠偏：资源类型短语默认走 search，而不是 generate_lesson_plan")
            result["intent"] = self.INTENT_SEARCH
            result["intents"] = [
                {"type": self.INTENT_SEARCH, "confidence": 0.95},
                {"type": self.INTENT_LESSON_PLAN, "confidence": 0.15},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.10},
                {"type": self.INTENT_CONVERSATION, "confidence": 0.10},
            ]
            if not result.get("user_needs"):
                result["user_needs"] = self._generate_user_needs(user_input, resource_types)
        
        # V41.1 改进：当用户输入包含资源获取指令词且资源类型为GGB时，优先使用search意图
        # 避免将"找ggb动画"误判为生成可视化设计建议
        user_input_lower = user_input.lower()
        has_resource_retrieval = any(keyword in user_input for keyword in ["想要", "需要", "找", "搜", "搜索", "查", "查找", "检索", "推荐", "有没有", "我要", "帮我找", "帮我搜"])
        has_ggb_type = any(rt.lower() == "ggb" for rt in resource_types)
        
        if has_resource_retrieval and has_ggb_type and result.get("intent") == self.INTENT_VISUALIZATION:
            print("🛠️ 意图纠偏：用户明确表示获取资源，将visualization改为search")
            result["intent"] = self.INTENT_SEARCH
            result["intents"] = [
                {"type": self.INTENT_SEARCH, "confidence": 0.95},
                {"type": self.INTENT_VISUALIZATION, "confidence": 0.20},
                {"type": self.INTENT_LESSON_PLAN, "confidence": 0.10},
                {"type": self.INTENT_CONVERSATION, "confidence": 0.10},
            ]
        
        return result

    def analyze(self, user_input: str, chat_history: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        分析用户输入，确定意图

        Args:
            user_input: 用户输入文本
            chat_history: 对话历史记录，用于上下文理解

        Returns:
            意图分析结果，包含 primary_intent 和 intents
        """
        print(f"\n====================================")
        print(f"[搜索] 意图理解开始")
        print(f"[习题] 用户输入：{user_input}")
        print(f"[教案] 对话历史：{len(chat_history) if chat_history else 0} 条")

        if not user_input or not user_input.strip():
            print("⚠️ 用户输入为空，使用默认意图")
            return self._build_conversation_result(
                user_input,
                confidence=0.95,
                user_needs="用户尚未提供有效输入，需要先通过对话确认需求",
            )

        # 保存对话历史到实例变量，供后续方法使用
        if chat_history:
            self.context_history = chat_history

        # V46.1修复：优先检查教案系统的特殊指令（在LLM之前）
        lesson_plan_special_commands = [
            "查看完整教案", "完整教案", "导出教案", 
            "导出为markdown", "导出为html", "导出为word",
            "修改教案", "调整教案"
        ]
        is_lesson_plan_command = any(cmd in user_input for cmd in lesson_plan_special_commands)
        if is_lesson_plan_command:
            print(f"🎯 V46.1检测到教案系统特殊指令，跳过LLM，直接使用关键词匹配")
            result = self._analyze_with_keywords(user_input)
            # 直接返回，不再执行后续的处理
            result["quantity_limit"] = self._extract_quantity_limit(user_input)
            result["grade_info"] = self._extract_grade_info(user_input)
            result["difficulty_info"] = self._extract_difficulty_info(user_input)
            result["clarified_topic"] = self._clarify_math_topic(user_input)
            result["context_analysis"] = self._analyze_context(user_input)
            result["courseware_teaching_use"] = self._extract_courseware_teaching_use(user_input)
            self._update_context_history(user_input, result)
            return result

        try:
            result = self._analyze_with_llm(user_input)
            print(f"✅ LLM 意图理解成功")
        except Exception as e:
            print(f"⚠️ LLM 意图理解失败：{e}")
            print("🔄 使用关键词匹配作为备用")
            result = self._analyze_with_keywords(user_input)

        # 无论使用 LLM 还是关键词匹配，都使用_extract_resource_types 方法来提取资源类型，确保准确性
        extracted_resource_types = self._extract_resource_types(user_input)
        if extracted_resource_types:
            result["resource_types"] = extracted_resource_types
            print(f"📋 提取的资源类型：{extracted_resource_types}")

        result = self._apply_intent_overrides(user_input, result)

        result["quantity_limit"] = self._extract_quantity_limit(user_input)
        result["grade_info"] = self._extract_grade_info(user_input)
        result["difficulty_info"] = self._extract_difficulty_info(user_input)
        result["clarified_topic"] = self._clarify_math_topic(user_input)
        result["context_analysis"] = self._analyze_context(user_input)
        # V53.0 新增：提取课件教学用途（新授课/练习课/复习课），供检索层过滤课件使用
        result["courseware_teaching_use"] = self._extract_courseware_teaching_use(user_input)

        print(f"📋 V33.0 数量限制：{result['quantity_limit']}")
        print(f"📋 V33.0 年级信息：{result['grade_info']}")
        print(f"📋 V33.0 难度信息：{result['difficulty_info']}")
        print(f"📋 V33.0 主题澄清：{result['clarified_topic']}")
        print(f"📋 上下文分析：{result['context_analysis']}")
        print(f"📋 V53.0 课件教学用途：{result['courseware_teaching_use']}")

        # 更新上下文历史
        self._update_context_history(user_input, result)

        return result
