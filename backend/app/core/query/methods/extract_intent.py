from .._shared import *


class _ExtractIntentMixin:
    def _extract_intent(self, original_query: str, cleaned_query: str, core_concepts: List[str]) -> Dict[str, Any]:
        """
        提取查询意图 - 四维分析
        """
        intent = {
            "topic": "",
            "resource_types": [],
            "operation": "",
            "quality": "",
            "instruction_type": ""
        }
        
        # 1. 识别指令类型
        instruction_type = self._identify_instruction_type(original_query)
        intent["instruction_type"] = instruction_type
        
        # 2. 提取主题（排除指令词的影响）
        if instruction_type:
            # 从指令词后的内容中提取主题
            topic = self._extract_topic_after_instruction(original_query, instruction_type)
        else:
            # 没有指令词，直接提取主题
            complete_theme = self._extract_complete_theme(original_query)
            if complete_theme:
                topic = complete_theme
            elif core_concepts:
                topic = core_concepts[0]
            else:
                topic = ""
        
        intent["topic"] = topic
        
        # 3. 提取资源类型
        # 首先，使用统一的资源类型配置来提取资源类型
        all_user_types = get_all_user_types()
        
        for user_type in all_user_types:
            if user_type in original_query:
                # 规范化为标准名称
                standard_name = get_standard_name(user_type)
                if standard_name not in intent["resource_types"]:
                    intent["resource_types"].append(standard_name)
                    logger.info(f"识别到资源类型: {user_type} -> {standard_name}")
        
        # 如果统一配置中没有找到，再用备用的模式匹配（保持兼容性）
        if not intent["resource_types"]:
            resource_type_patterns = {
                "courseware": ["课件", "ppt", "幻灯片"],
                "lesson_plan": ["教案", "教学设计", "导学案"],
                "exercise": ["习题", "题目", "练习题", "试题", "题"],
                "lesson_case": ["课例", "视频", "课堂实录", "公开课"],
                "ggb": ["ggb", "GGB", "geogebra", "几何画板"],
                "syllabus": ["教学大纲", "大纲", "课程标准"],
                "theory": ["理论", "知识点", "概念"]
            }
            
            for resource_type, keywords in resource_type_patterns.items():
                for keyword in keywords:
                    if keyword in original_query:
                        # 这里提取的是数据库类型，我们需要将它映射到标准名称
                        # 从DB类型到标准名称的映射
                        db_to_std = {
                            "lesson_plan": "教案",
                            "courseware": "课件",
                            "lesson_case": "课例",
                            "exercise": "习题",
                            "ggb": "GGB",
                            "syllabus": "教学大纲",
                            "theory": "理论"
                        }
                        standard_name = db_to_std.get(resource_type, resource_type)
                        if standard_name not in intent["resource_types"]:
                            intent["resource_types"].append(standard_name)
                            logger.info(f"备用模式识别资源类型: {resource_type} -> {standard_name}")
                        break
        
        # 4. 提取操作类型
        operation_patterns = {
            "学习": ["学习", "学", "了解", "理解", "掌握"],
            "备课": ["备课", "准备", "教学设计"],
            "出题": ["出题", "组题", "命题", "找题"],
            "练习": ["练习", "做题", "训练", "巩固"],
            "复习": ["复习", "回顾", "总结"],
            "预习": ["预习", "提前学"]
        }
        
        for operation, keywords in operation_patterns.items():
            for keyword in keywords:
                if keyword in original_query:
                    intent["operation"] = operation
                    break
            if intent["operation"]:
                break
        
        # 5. 提取质量要求
        quality_patterns = {
            "基础": ["基础", "简单", "容易", "入门"],
            "中等": ["中等", "一般", "普通"],
            "拔高": ["拔高", "难", "困难", "挑战", "培优", "提高"],
            "优秀": ["优秀", "精品", "优质", "获奖", "名师"]
        }
        
        for quality, keywords in quality_patterns.items():
            for keyword in keywords:
                if keyword in original_query:
                    intent["quality"] = quality
                    break
            if intent["quality"]:
                break
        
        return intent
