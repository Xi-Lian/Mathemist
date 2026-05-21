from .._shared import *


class _AnalyzeWithKeywordsMixin:
    def _analyze_with_keywords(self, user_input: str) -> Dict[str, Any]:
        """
        使用关键词匹配进行意图理解
        
        Args:
            user_input: 用户输入
        
        Returns:
            意图分析结果
        """
        user_input_lower = user_input.lower()
        
        # V46.1修复：优先检查教案系统的特殊指令
        # 这些指令应该直接进入教案系统，而不是资源检索
        lesson_plan_special_commands = [
            "查看完整教案", "完整教案", "导出教案", 
            "导出为markdown", "导出为html", "导出为word",
            "修改教案", "调整教案"
        ]
        is_lesson_plan_command = any(cmd in user_input for cmd in lesson_plan_special_commands)
        if is_lesson_plan_command:
            print(f"🎯 V46.1检测到教案系统特殊指令，强制使用generate_lesson_plan意图")
            return self._get_single_intent_result(
                self.INTENT_LESSON_PLAN,
                "检测到教案系统特殊指令",
                "用户需要查看/导出/修改已生成的教案",
                []
            )
        
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
        
        prefer_search_for_resource_request = self._should_prefer_search_for_resource_request(user_input, resource_types)
        print(f"📋 资源型短语优先搜索: {prefer_search_for_resource_request}")

        # 确定意图
        # 优先级：修改意见 > 明确生成 > 资源获取 > 资源型短语默认搜索 > 关键词
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
        elif prefer_search_for_resource_request:
            print("🎯 识别到资源型短语，默认使用search意图")
            return self._get_single_intent_result(
                self.INTENT_SEARCH,
                "识别到资源型短语",
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
