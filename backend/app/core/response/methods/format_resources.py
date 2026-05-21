from .._shared import *


class _FormatResourcesMixin:
    def _format_resources(self, state: Any, scenario: str = "search") -> str:
        """
        格式化检索到的资源
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景
        
        Returns:
            格式化的资源文本
        """
        print(f"📋 资源格式化场景: {scenario}")
        
        # 获取内容处理器
        if self.content_processor is None:
            self.content_processor = self.model_config.get_content_processor()
        
        # 获取检索到的资源
        retrieved_resources = self._get_state_value(state, "retrieved_resources", {})
        
        # 检查是否为 None
        if retrieved_resources is None:
            retrieved_resources = {}
        
        # 获取用户需求
        user_needs = self._get_state_value(state, "user_needs", "")
        resource_types = self._get_state_value(state, "resource_types", [])
        user_input = self._get_state_value(state, "user_input", "")
        
        # 从用户输入中提取资源类型
        if not resource_types and user_input:
            # 常见资源类型关键词
            resource_keywords = {
                "教案": ["教案", "教学设计", "教学方案"],
                "习题": ["习题", "练习题", "试题", "题目"],
                "课件": ["课件", "PPT", "幻灯片"],
                "课例": ["课例", "教学视频", "课堂实录", "视频", "微课", "优质课"],
                "GGB": ["GGB", "几何画板"],
                "教学大纲": ["教学大纲", "大纲"]
            }
            
            # 检查用户输入中是否包含资源类型关键词
            for resource_type, keywords in resource_keywords.items():
                for keyword in keywords:
                    if keyword in user_input:
                        resource_types.append(resource_type)
                        break
            
            # 去重
            resource_types = list(set(resource_types))
        
        print(f"📋 用户需求: {user_needs}")
        print(f"📋 资源类型: {resource_types}")
        
        response_parts = []
        
        # 检查用户是否指定了"资料"或"资源"（表示要所有资源）
        is_all_resources = any(rt in ["资料", "资源"] for rt in resource_types)
        
        # 如果用户明确指定了资源类型，只输出指定的类型
        if resource_types and not is_all_resources:
            print(f"🎯 用户明确指定了资源类型，只输出指定类型")
            print(f"   用户指定类型: {resource_types}")
            
            # 输出用户指定的资源类型
            for user_type in resource_types:
                # 使用统一的资源类型映射
                mapping = get_resource_type_mapping(user_type)
                if mapping:
                    standard_name, db_type, category_key, icon = mapping
                    # 特殊处理：如果category_key是"all_resources"，则输出所有资源
                    if category_key == "all_resources":
                        print(f"   🎯 类型: {user_type} -> {standard_name}，输出所有资源")
                        
                        # 格式化教案资源
                        lesson_plans = retrieved_resources.get("lesson_plan_patterns", [])
                        if lesson_plans:
                            response_parts.append(self._format_resource_category(
                                "教案资源", 
                                lesson_plans,
                                "📚",
                                scenario,
                                state
                            ))
                        
                        # 格式化习题资源
                        exercises = retrieved_resources.get("exercise_resources", [])
                        if exercises:
                            response_parts.append(self._format_resource_category(
                                "习题资源",
                                exercises,
                                "📝",
                                scenario,
                                state
                            ))
                        
                        # 格式化课件资源
                        coursewares = retrieved_resources.get("courseware_resources", [])
                        if coursewares:
                            response_parts.append(self._format_resource_category(
                                "课件资源",
                                coursewares,
                                "📊",
                                scenario,
                                state
                            ))
                        
                        # 格式化课例资源
                        lesson_cases = retrieved_resources.get("lesson_case_resources", [])
                        if lesson_cases:
                            response_parts.append(self._format_resource_category(
                                "课例资源",
                                lesson_cases,
                                "🎬",
                                scenario,
                                state
                            ))
                        
                        # 格式化GGB资源
                        ggbs = retrieved_resources.get("ggb_resources", [])
                        if ggbs:
                            response_parts.append(self._format_resource_category(
                                "GGB资源",
                                ggbs,
                                "🔧",
                                scenario,
                                state
                            ))
                        
                        # 格式化教学大纲
                        syllabi = retrieved_resources.get("syllabus_resources", [])
                        if syllabi:
                            response_parts.append(self._format_resource_category(
                                "教学大纲",
                                syllabi,
                                "📋",
                                scenario,
                                state
                            ))
                        
                        # 格式化可视化示例
                        visualizations = retrieved_resources.get("visualization_examples", [])
                        if visualizations:
                            response_parts.append(self._format_resource_category(
                                "可视化示例",
                                visualizations,
                                "🎨",
                                scenario,
                                state
                            ))
                    else:
                        resources = retrieved_resources.get(category_key, [])
                        if resources:
                            response_parts.append(self._format_resource_category(
                                f"{standard_name}资源", 
                                resources,
                                icon,
                                scenario,
                                state
                            ))
                            print(f"   ✓ 处理类型: {user_type} -> {standard_name} ({len(resources)}条)")
                        else:
                            print(f"   ⚠️ 类型: {user_type} -> {standard_name}，无资源")
                else:
                    print(f"   ⚠️ 未知类型: {user_type}，跳过")
            
            # 如果没有找到任何资源
            if not response_parts:
                response_parts.append(f"未找到{', '.join(resource_types)}相关的资源")
        
        else:
            # 用户没有明确指定资源类型，或者指定了"资料"/"资源"，输出所有找到的资源
            if is_all_resources:
                print(f"🎯 用户指定了'资料'或'资源'，输出所有找到的资源")
            else:
                print(f"🔍 用户未指定资源类型，输出所有找到的资源")
            
            # 格式化教案资源
            lesson_plans = retrieved_resources.get("lesson_plan_patterns", [])
            if lesson_plans:
                response_parts.append(self._format_resource_category(
                    "教案资源", 
                    lesson_plans,
                    "📚",
                    scenario,
                    state
                ))
            
            # 格式化习题资源
            exercises = retrieved_resources.get("exercise_resources", [])
            if exercises:
                response_parts.append(self._format_resource_category(
                    "习题资源",
                    exercises,
                    "📝",
                    scenario,
                    state
                ))
            
            # 格式化课件资源
            coursewares = retrieved_resources.get("courseware_resources", [])
            if coursewares:
                response_parts.append(self._format_resource_category(
                    "课件资源",
                    coursewares,
                    "📊",
                    scenario,
                    state
                ))
            
            # 格式化课例资源
            lesson_cases = retrieved_resources.get("lesson_case_resources", [])
            if lesson_cases:
                response_parts.append(self._format_resource_category(
                    "课例资源",
                    lesson_cases,
                    "🎬",
                    scenario,
                    state
                ))
            
            # 格式化GGB资源
            ggbs = retrieved_resources.get("ggb_resources", [])
            if ggbs:
                response_parts.append(self._format_resource_category(
                    "GGB资源",
                    ggbs,
                    "🔧",
                    scenario,
                    state
                ))
            
            # 格式化教学大纲
            syllabi = retrieved_resources.get("syllabus_resources", [])
            if syllabi:
                response_parts.append(self._format_resource_category(
                    "教学大纲",
                    syllabi,
                    "📋",
                    scenario,
                    state
                ))
            
            # 格式化可视化示例
            visualizations = retrieved_resources.get("visualization_examples", [])
            if visualizations:
                response_parts.append(self._format_resource_category(
                    "可视化示例",
                    visualizations,
                    "🎨",
                    scenario,
                    state
                ))
            
            # 注意：理论资源不推送给用户，仅用于教案生成
            # 理论资源在教案生成时会被使用，但不会在响应中显示
        
        return "\n".join(response_parts) if response_parts else "未找到相关资源"
