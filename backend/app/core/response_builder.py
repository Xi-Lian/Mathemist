"""
响应生成模块

职责：
- 根据意图和生成的结果构建最终响应
- 整合教案、可视化建议和检索到的资源
- 提供结构化的响应输出
- V33.0改进：添加超时处理和降级方案

依赖：
- model_config (模型配置)
- smart_content_processor (内容处理)
"""

import time
from typing import Dict, Any, List
from .model_config import model_config
from ..smart_content_processor import SmartContentProcessor
from ..config.resource_type_config import (
    get_response_field,
    get_icon,
    get_standard_name,
    get_resource_type_mapping
)


class ResponseBuilder:
    """响应构建器"""
    
    def __init__(self):
        """初始化响应构建器"""
        self.model_config = model_config
        self.content_processor = None
        self.timeout = 30  # V33.0改进：设置超时时间为30秒
        self.start_time = None  # V33.0改进：记录开始时间
    
    def build(self, state: Any) -> str:
        """
        构建最终响应
        
        Args:
            state: 状态对象，包含意图、教案、建议等（可以是 MathAgentState 对象或字典）
        
        Returns:
            格式化的响应文本
        """
        print(f"\n====================================")
        print(f"📤 响应生成开始")
        
        # V33.0改进：记录开始时间
        self.start_time = time.time()
        
        try:
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 检查意图类型
            if hasattr(state, 'intent'):
                intent = state.intent
            else:
                intent = state.get("intent", "search")
            
            # 对于搜索意图，不使用已有的 response，而是重新构建响应
            # 这样可以确保使用最新的分层展示逻辑
            if intent == "search":
                print(f"🔀 搜索意图，重新构建响应以使用最新的分层展示逻辑")
                response = self._build_search_response(state)
                print(f"✅ 响应生成成功，长度: {len(response)}字符")
                return response
            
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 优先检查是否已经有响应（非搜索意图）
            response = self._get_state_value(state, "response", "")
            if response:
                print(f"🔀 发现已有响应，直接返回")
                print(f"✅ 响应生成成功，长度: {len(response)}字符")
                return response
            
            # V33.0改进：检查是否超时
            if self._check_timeout():
                print(f"⚠️ 响应生成超时，使用降级方案")
                return self._get_timeout_response()
            
            # 检查是否有多个处理过的意图
            processed_intents = self._get_state_value(state, "processed_intents", [])
            
            if processed_intents and len(processed_intents) > 1:
                print(f"🎯 检测到多意图处理结果: {processed_intents}")
                response = self._build_multi_intent_response(state, processed_intents)
            else:
                # 单个意图处理
                if hasattr(state, 'intent'):
                    intent = state.intent
                else:
                    intent = state.get("intent", "search")
                print(f"🎯 单个意图: {intent}")
                
                if intent == "generate_lesson_plan":
                    response = self._build_lesson_plan_response(state)
                elif intent == "visualization":
                    response = self._build_visualization_response(state)
                else:
                    response = self._build_search_response(state)
            
            print(f"✅ 响应生成成功，长度: {len(response)}字符")
            
            return response
            
        except Exception as e:
            print(f"❌ 响应生成失败: {str(e)}")
            return self._get_error_response(str(e))
    
    def _build_multi_intent_response(self, state: Any, processed_intents: list) -> str:
        """
        构建多意图响应
        
        Args:
            state: 状态对象
            processed_intents: 已处理的意图列表
        
        Returns:
            整合后的响应文本
        """
        response_parts = []
        
        # 添加多意图处理说明
        response_parts.append("🎯 **智能助手为您提供多维度服务**\n")
        
        # 按优先级添加各意图的响应内容
        # 1. 教案生成内容
        if "generate_lesson_plan" in processed_intents:
            lesson_plan = self._get_state_value(state, "lesson_plan", "")
            if lesson_plan:
                response_parts.append("\n" + "="*50)
                response_parts.append("📚 **生成的教案**")
                response_parts.append("="*50)
                response_parts.append(lesson_plan)
        
        # 2. 可视化建议内容
        if "visualization" in processed_intents:
            suggestions = self._get_state_value(state, "visualization_suggestions", "")
            if suggestions:
                response_parts.append("\n" + "="*50)
                response_parts.append("🎨 **可视化设计建议**")
                response_parts.append("="*50)
                response_parts.append(suggestions)
        
        # 3. GGB设计建议内容
        if "ggb_design" in processed_intents:
            ggb_suggestions = self._get_state_value(state, "ggb_design_suggestions", None)
            if ggb_suggestions:
                response_parts.append("\n" + "="*50)
                response_parts.append("🔧 **GeoGebra动态图设计建议**")
                response_parts.append("="*50)
                for i, suggestion in enumerate(ggb_suggestions, 1):
                    if suggestion.get("error"):
                        response_parts.append(f"❌ 第{i}个GGB资源设计建议生成失败: {suggestion.get('error')}")
                    else:
                        response_parts.append(f"\n### {i}. {suggestion.get('metadata', {}).get('ggb_filename', '未知')}")
                        response_parts.append(suggestion.get("design_steps", ""))
        
        # 4. 添加检索到的资源
        # 根据是否包含教案生成意图来决定场景
        resource_scenario = "generation" if "generate_lesson_plan" in processed_intents else "search"
        resources = self._format_resources(state, scenario=resource_scenario)
        if resources:
            response_parts.append("\n" + "="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
    def _build_lesson_plan_response(self, state: Any) -> str:
        """
        构建教案生成响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            教案响应文本
        """
        response_parts = []
        
        # 优先检查是否有引导响应（当信息不完整时）
        response = self._get_state_value(state, "response", "")
        if response:
            # 如果有引导响应，直接返回引导信息
            return response
        
        # 添加教案
        lesson_plan = self._get_state_value(state, "lesson_plan", "")
        if lesson_plan:
            response_parts.append("="*50)
            response_parts.append("📚 **生成的教案**")
            response_parts.append("="*50)
            response_parts.append(lesson_plan)
            response_parts.append("\n")
        
        # 添加检索到的资源
        resources = self._format_resources(state, scenario="generation")
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
    def _build_visualization_response(self, state: Any) -> str:
        """
        构建可视化建议响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            可视化响应文本
        """
        response_parts = []
        
        # 添加GGB设计建议（优先）
        ggb_suggestions = self._get_state_value(state, "ggb_design_suggestions", None)
        if ggb_suggestions:
            response_parts.append("="*50)
            response_parts.append("🎨 **GeoGebra动态图设计建议**")
            response_parts.append("="*50)
            for i, suggestion in enumerate(ggb_suggestions, 1):
                if suggestion.get("error"):
                    response_parts.append(f"❌ 第{i}个GGB资源设计建议生成失败: {suggestion.get('error')}\n")
                else:
                    response_parts.append(f"\n### {i}. {suggestion.get('metadata', {}).get('ggb_filename', '未知')}")
                    response_parts.append(suggestion.get("design_steps", ""))
                    response_parts.append("\n---")
        
        # 添加可视化建议
        suggestions = self._get_state_value(state, "visualization_suggestions", "")
        if suggestions:
            response_parts.append("\n" + "="*50)
            response_parts.append("🎨 **可视化设计建议**")
            response_parts.append("="*50)
            response_parts.append(suggestions)
            response_parts.append("\n")
        
        # 添加检索到的资源
        resources = self._format_resources(state, scenario="search")
        if resources:
            response_parts.append("="*50)
            response_parts.append("📋 **相关教学资源**")
            response_parts.append("="*50)
            response_parts.append(resources)
        
        return "\n".join(response_parts)
    
    def _build_search_response(self, state: Any) -> str:
        """
        构建资源搜索响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            搜索响应文本
        """
        # 对于搜索意图，只显示检索到的资源，不显示生成的内容
        # 确保主次分明，避免生成内容干扰用户对检索结果的判断
        return self._format_resources(state, scenario="search")
    
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
    
    def _classify_resource_domain(self, resource: Dict[str, Any]) -> str:
        """
        根据教案标题和内容判断所属领域
        
        Args:
            resource: 资源字典
            
        Returns:
            领域名称：一般函数、具体函数、三角函数、其他
        """
        title = resource.get("title", "")
        content = resource.get("content", "")
        source = resource.get("source", "")
        
        # 合并所有文本内容
        full_text = f"{title} {content} {source}"
        
        # 判断领域
        if any(keyword in full_text for keyword in ["三角函数", "正弦函数", "余弦函数", "正切函数", "诱导公式", "三角"]):
            return "三角函数"
        elif any(keyword in full_text for keyword in ["指数函数", "对数函数", "幂函数"]):
            return "具体函数"
        elif any(keyword in full_text for keyword in ["函数的基本性质", "函数的性质", "单调性", "奇偶性", "周期性", "函数的概念", "函数概念"]) and "三角" not in full_text:
            return "一般函数"
        else:
            return "其他"
    
    def _get_priority_domains(self, query: str) -> List[str]:
        """
        根据用户查询确定优先领域
        
        Args:
            query: 用户查询
            
        Returns:
            优先领域列表
        """
        if not query:
            return []
        
        query_lower = query.lower()
        priority_domains = []
        
        # 主题到领域的映射
        theme_domain_map = {
            "函数的概念": "一般函数",
            "函数的表示法": "一般函数",
            "函数的性质": "一般函数",
            "单调性": "一般函数",
            "奇偶性": "一般函数",
            "周期性": "一般函数",
            "指数函数": "具体函数",
            "对数函数": "具体函数",
            "幂函数": "具体函数",
            "三角函数": "三角函数",
            "正弦函数": "三角函数",
            "余弦函数": "三角函数",
            "正切函数": "三角函数",
        }
        
        # 检查查询中包含的主题
        for theme, domain in theme_domain_map.items():
            if theme in query_lower:
                if domain not in priority_domains:
                    priority_domains.append(domain)
        
        # 特殊处理：检查具体函数的概念
        if "指数函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "对数函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "幂函数" in query_lower:
            if "具体函数" not in priority_domains:
                priority_domains.append("具体函数")
        elif "三角函数" in query_lower:
            if "三角函数" not in priority_domains:
                priority_domains.append("三角函数")
        elif "函数" in query_lower:
            if "一般函数" not in priority_domains:
                priority_domains.append("一般函数")
        
        return priority_domains
    
    def _is_parallel_query(self, state: Any) -> bool:
        """
        判断是否为多主题并列查询（包含"和"、"与"、"及"等并列词）
        
        Args:
            state: 状态对象
            
        Returns:
            是否为多主题并列查询
        """
        user_input = self._get_state_value(state, "user_input", "")
        if not user_input:
            return False
        
        # 并列词列表
        parallel_keywords = ["和", "与", "及", "以及", "还有", "加上"]
        
        # 检查是否包含并列词
        for keyword in parallel_keywords:
            if keyword in user_input:
                print(f"🔀 检测到并列词 '{keyword}'，判断为多主题并列查询")
                return True
        
        return False
    
    def _calculate_query_specificity(self, query: str) -> float:
        """
        计算查询的具体程度
        
        Args:
            query: 用户查询
            
        Returns:
            具体程度分数 (0-1)
        """
        if not query:
            return 0.0
        
        # 关键词数量
        words = query.split()
        word_count = len(words)
        
        # 具体关键词权重
        specific_keywords = [
            "概念", "性质", "图像", "应用", "计算", "公式", "定理",
            "单调性", "奇偶性", "周期性", "定义域", "值域", "最大值", "最小值"
        ]
        
        # 计算具体程度分数
        specificity = 0.0
        
        # 基于词数的分数 (0-0.5)
        if word_count >= 5:
            specificity += 0.5
        elif word_count >= 3:
            specificity += 0.3
        elif word_count >= 2:
            specificity += 0.1
        
        # 基于具体关键词的分数 (0-0.5)
        for keyword in specific_keywords:
            if keyword in query:
                specificity += 0.1
                if specificity >= 1.0:
                    break
        
        return min(1.0, specificity)
    
    def _generate_dynamic_categories(self, query: str, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        V10.0：动态聚类，根据查询自动调整分类粒度
        
        改进：
        - 集成多维度评估结果到分类决策
        - 确保评估与分类系统协同工作
        """
        # 确保所有资源都有综合得分
        for resource in resources:
            if "overall_score" not in resource:
                resource["overall_score"] = self._calculate_multi_dimension_score(resource)
        
        # 计算查询的具体程度
        specificity = self._calculate_query_specificity(query)
        
        # 根据具体程度确定分类策略
        if specificity >= 0.7:  # 高度具体的查询
            return self._generate_fine_grained_categories(resources)
        elif specificity >= 0.3:  # 中等具体的查询
            return self._generate_medium_grained_categories(resources)
        else:  # 一般查询
            return self._generate_coarse_grained_categories(resources)
    
    def _generate_coarse_grained_categories(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成粗粒度分类 - 连续谱系版本
        """
        if not resources:
            return {
                "核心资源": [],
                "相关资源": [],
                "扩展资源": []
            }
        
        # 计算得分范围
        scores = [resource.get("overall_score", resource.get("relevance", 0)) for resource in resources]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        # 基于连续分布的分类阈值
        core_threshold = max_score - score_range * 0.3  # 前30%为核心资源
        related_threshold = max_score - score_range * 0.7  # 30%-70%为相关资源
        
        categories = {
            "核心资源": [],
            "相关资源": [],
            "扩展资源": []
        }
        
        for resource in resources:
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            if overall_score >= core_threshold:
                categories["核心资源"].append(resource)
            elif overall_score >= related_threshold:
                categories["相关资源"].append(resource)
            else:
                categories["扩展资源"].append(resource)
        
        # 确保核心资源至少有一个（如果有资源的话）
        if not categories["核心资源"] and resources:
            categories["核心资源"].append(resources[0])
            if categories["相关资源"]:
                categories["相关资源"].pop(0)
        
        return categories
    
    def _generate_medium_grained_categories(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成中等粒度分类 - 连续谱系版本
        """
        if not resources:
            return {
                "核心主题资源": [],
                "相关主题资源": [],
                "扩展主题资源": []
            }
        
        # 计算得分范围
        scores = [resource.get("overall_score", resource.get("relevance", 0)) for resource in resources]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        # 基于连续分布的分类阈值
        core_threshold = max_score - score_range * 0.3  # 前30%为核心资源
        related_threshold = max_score - score_range * 0.7  # 30%-70%为相关资源
        
        categories = {
            "核心主题资源": [],
            "相关主题资源": [],
            "扩展主题资源": []
        }
        
        for resource in resources:
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            match_level = resource.get("match_level", "none")
            
            if match_level == "core" or overall_score >= core_threshold:
                categories["核心主题资源"].append(resource)
            elif match_level == "related" or overall_score >= related_threshold:
                categories["相关主题资源"].append(resource)
            else:
                categories["扩展主题资源"].append(resource)
        
        # 确保核心主题资源至少有一个（如果有资源的话）
        if not categories["核心主题资源"] and resources:
            categories["核心主题资源"].append(resources[0])
            if categories["相关主题资源"]:
                categories["相关主题资源"].pop(0)
        
        return categories
    
    def _generate_fine_grained_categories(self, resources: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        生成细粒度分类 - 连续谱系版本
        """
        if not resources:
            return {
                "核心概念资源": [],
                "重点性质资源": [],
                "应用实例资源": [],
                "扩展参考资源": []
            }
        
        # 计算得分范围
        scores = [resource.get("overall_score", resource.get("relevance", 0)) for resource in resources]
        max_score = max(scores)
        min_score = min(scores)
        score_range = max_score - min_score if max_score > min_score else 1.0
        
        # 基于连续分布的分类阈值
        high_threshold = max_score - score_range * 0.4  # 前40%为高相关资源
        medium_threshold = max_score - score_range * 0.7  # 40%-70%为中等相关资源
        
        categories = {
            "核心概念资源": [],
            "重点性质资源": [],
            "应用实例资源": [],
            "扩展参考资源": []
        }
        
        for resource in resources:
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            title = resource.get("title", "")
            content = resource.get("content", "")
            
            # 基于内容特征进行细粒度分类
            full_text = f"{title} {content}"
            
            if overall_score >= high_threshold:
                if any(keyword in full_text for keyword in ["概念", "定义", "含义"]):
                    categories["核心概念资源"].append(resource)
                elif any(keyword in full_text for keyword in ["性质", "定理", "法则"]):
                    categories["重点性质资源"].append(resource)
                elif any(keyword in full_text for keyword in ["应用", "实例", "例子"]):
                    categories["应用实例资源"].append(resource)
                else:
                    categories["核心概念资源"].append(resource)
            elif overall_score >= medium_threshold:
                if any(keyword in full_text for keyword in ["概念", "定义"]):
                    categories["核心概念资源"].append(resource)
                elif any(keyword in full_text for keyword in ["性质", "定理"]):
                    categories["重点性质资源"].append(resource)
                elif any(keyword in full_text for keyword in ["应用", "实例"]):
                    categories["应用实例资源"].append(resource)
                else:
                    categories["扩展参考资源"].append(resource)
            else:
                categories["扩展参考资源"].append(resource)
        
        return categories
    
    def _record_user_feedback(self, resource_id: str, action: str, context: Dict[str, Any]):
        """
        V10.0：记录用户行为反馈
        
        Args:
            resource_id: 资源ID
            action: 用户行为（click, view, download, etc.）
            context: 上下文信息
        """
        # 这里可以实现具体的反馈记录逻辑
        # 例如：存储到数据库、缓存或日志文件
        print(f"📊 记录用户反馈: {action} - {resource_id}")
        # 实际实现中，这里应该调用相应的存储服务
    
    def _analyze_feedback_data(self, resource_id: str) -> Dict[str, float]:
        """
        V10.0：分析用户反馈数据
        
        Args:
            resource_id: 资源ID
            
        Returns:
            反馈分析结果
        """
        # 这里可以实现具体的反馈分析逻辑
        # 例如：从数据库或缓存中读取反馈数据并分析
        # 为了演示，返回模拟数据
        return {
            "click_rate": 0.75,
            "view_duration": 0.8,
            "download_rate": 0.4,
            "satisfaction_score": 0.85
        }
    
    def _optimize_ranking_with_feedback(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        V10.0：使用用户反馈优化排序
        
        Args:
            resources: 资源列表
            
        Returns:
            优化排序后的资源列表
        """
        # 为每个资源添加反馈得分
        for resource in resources:
            resource_id = resource.get("id", str(hash(resource.get("title", ""))))
            feedback_data = self._analyze_feedback_data(resource_id)
            
            # 计算反馈得分
            feedback_score = (
                feedback_data.get("click_rate", 0.5) * 0.3 +
                feedback_data.get("view_duration", 0.5) * 0.2 +
                feedback_data.get("download_rate", 0.5) * 0.3 +
                feedback_data.get("satisfaction_score", 0.5) * 0.2
            )
            
            # 结合反馈得分优化综合得分
            overall_score = resource.get("overall_score", resource.get("relevance", 0))
            optimized_score = overall_score * 0.7 + feedback_score * 0.3
            resource["optimized_score"] = optimized_score
        
        # 基于优化后的得分排序
        sorted_resources = sorted(
            resources,
            key=lambda x: (-x.get("optimized_score", x.get("overall_score", 0)),
                          -x.get("overall_score", x.get("relevance", 0)))
        )
        
        return sorted_resources
    
    def _calculate_multi_dimension_score(self, resource: Dict[str, Any]) -> float:
        """
        V10.0：计算多维度综合得分
        
        Args:
            resource: 资源字典
            
        Returns:
            综合得分
        """
        # 从资源中提取各项指标
        relevance = resource.get("relevance", resource.get("relevance_score", 0))
        
        # 优先使用主题匹配器计算的评估指标
        resource_quality = resource.get("resource_quality", None)
        content_completeness = resource.get("content_completeness", None)
        teaching_value = resource.get("teaching_value", None)
        comprehensiveness = resource.get("comprehensiveness", None)
        
        # 如果没有评估指标，使用默认值
        if resource_quality is None:
            resource_quality = 0.5
        if content_completeness is None:
            content_completeness = 0.5
        if teaching_value is None:
            teaching_value = 0.5
        if comprehensiveness is None:
            comprehensiveness = 0.5
        
        # 权重配置
        weights = {
            "relevance": 0.4,      # 相关性权重
            "quality": 0.2,        # 资源质量权重
            "completeness": 0.15,  # 内容完整性权重
            "teaching": 0.15,      # 教学价值权重
            "comprehensive": 0.1   # 综合性权重
        }
        
        # 计算加权和
        total_score = (
            relevance * weights["relevance"] +
            resource_quality * weights["quality"] +
            content_completeness * weights["completeness"] +
            teaching_value * weights["teaching"] +
            comprehensiveness * weights["comprehensive"]
        )
        
        return total_score
    
    def _calculate_unified_score(self, resource: Dict[str, Any]) -> Dict[str, Any]:
        """
        V11.0：统一决策中心 - 综合所有评估信息计算最终得分
        
        决策规则：
        1. 优先级层级（决定基础分区间）：
           - 精确匹配：0.90-1.00
           - 直接相关：0.75-0.89
           - 间接相关：0.60-0.74
           - 背景提及：0.40-0.59
        
        2. 在同一优先级内，综合以下因素调整分数：
           - 相关性分数（向量相似度）
           - 概念距离因子（层级关系）
           - 资源质量指标
           - 多维度评估指标
        
        Args:
            resource: 资源字典
            
        Returns:
            包含最终得分和决策信息的字典
        """
        # 提取关键信息
        match_level = resource.get("match_level", "none")
        is_core_match = resource.get("is_core_match", False)
        relevance = resource.get("relevance", resource.get("relevance_score", 0))
        
        # V11.2：提取多维度评估指标（使用0.0作为默认值，以反映真实的计算结果）
        resource_quality = resource.get("resource_quality", 0.0)
        content_completeness = resource.get("content_completeness", 0.0)
        teaching_value = resource.get("teaching_value", 0.0)
        comprehensiveness = resource.get("comprehensiveness", 0.0)
        
        # V11.2：提取概念层级信息（使用0.5作为默认值，表示中性）
        concept_hierarchy_factor = resource.get("concept_hierarchy_factor", 0.5)
        
        # ===== 第一步：确定优先级层级和基础分 =====
        # V11.1：修复优先级层级定义，与主题匹配器的输出保持一致
        if match_level == "core" or is_core_match:
            # 第一优先级：核心主题匹配（精确命中用户查询）
            priority_level = 4
            base_score_min = 0.90
            base_score_max = 1.00
            priority_name = "核心主题匹配"
        elif match_level == "related":
            # 第二优先级：相关主题匹配（同一概念的不同方面）
            priority_level = 3
            base_score_min = 0.75
            base_score_max = 0.89
            priority_name = "相关主题匹配"
        elif match_level == "extended":
            # 第三优先级：扩展主题匹配（同一领域的不同概念）
            priority_level = 2
            base_score_min = 0.60
            base_score_max = 0.74
            priority_name = "扩展主题匹配"
        elif match_level == "mentioned":
            # 第四优先级：提及主题匹配（仅作为背景提及）
            priority_level = 1
            base_score_min = 0.40
            base_score_max = 0.59
            priority_name = "提及主题匹配"
        else:
            # 无匹配
            priority_level = 0
            base_score_min = 0.0
            base_score_max = 0.39
            priority_name = "无匹配"
        
        # ===== 第二步：计算调整因子 =====
        # 相关性因子（在基础分区间内调整）
        relevance_factor = relevance * 0.3  # 贡献最多30%的调整
        
        # 概念距离因子（层级关系）
        hierarchy_adjustment = (concept_hierarchy_factor - 0.5) * 0.2  # 贡献±10%的调整
        
        # 资源质量因子
        quality_score = (
            resource_quality * 0.3 +
            content_completeness * 0.25 +
            teaching_value * 0.25 +
            comprehensiveness * 0.2
        )
        quality_factor = (quality_score - 0.5) * 0.2  # 贡献±10%的调整
        
        # ===== 第三步：计算最终得分 =====
        # 在基础分区间内进行调整
        score_range = base_score_max - base_score_min
        adjustment = (relevance_factor + hierarchy_adjustment + quality_factor) * score_range
        final_score = base_score_min + score_range * 0.5 + adjustment
        
        # 确保分数在合理范围内
        final_score = max(base_score_min, min(base_score_max, final_score))
        
        # ===== 第四步：记录决策信息 =====
        decision_info = {
            "priority_level": priority_level,
            "priority_name": priority_name,
            "base_score_range": [base_score_min, base_score_max],
            "relevance_factor": round(relevance_factor, 3),
            "hierarchy_adjustment": round(hierarchy_adjustment, 3),
            "quality_factor": round(quality_factor, 3),
            "final_score": round(final_score, 3)
        }
        
        return {
            "final_score": final_score,
            "priority_level": priority_level,
            "priority_name": priority_name,
            "decision_info": decision_info
        }
    
    def _sort_resources_globally(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        V11.0：基于统一决策中心的全局排序
        
        排序规则：
        1. 首先按优先级层级排序（精确匹配 > 直接相关 > 间接相关 > 背景提及）
        2. 同一优先级内按最终得分排序
        3. 得分相同则按相关性排序
        
        Args:
            resources: 资源列表
            
        Returns:
            排序后的资源列表
        """
        # 为每个资源计算统一决策得分
        print(f"\n🔢 统一决策中心：处理 {len(resources)} 个资源")
        for i, resource in enumerate(resources):
            decision_result = self._calculate_unified_score(resource)
            resource["final_score"] = decision_result["final_score"]
            resource["priority_level"] = decision_result["priority_level"]
            resource["priority_name"] = decision_result["priority_name"]
            resource["decision_info"] = decision_result["decision_info"]
            
            # 同时更新overall_score保持一致性
            resource["overall_score"] = decision_result["final_score"]
            
            # V11.1：添加调试日志，显示前3个资源的决策信息
            if i < 3:
                print(f"  资源 {i+1}: {resource.get('title', '未知')[:30]}...")
                print(f"    - 匹配级别: {resource.get('match_level', 'none')} -> 优先级: {decision_result['priority_name']}")
                print(f"    - 基础分区间: {decision_result['decision_info']['base_score_range']}")
                print(f"    - 最终得分: {decision_result['final_score']:.3f}")
                print(f"    - 概念层级因子: {resource.get('concept_hierarchy_factor', 0.5):.3f}")
                print(f"    - 资源质量: {resource.get('resource_quality', 0.5):.3f}")
        
        # 基于统一决策结果排序
        # 排序键：(-优先级层级, -最终得分, -相关性, -核心匹配, -匹配主题数)
        sorted_resources = sorted(
            resources,
            key=lambda x: (
                -x.get("priority_level", 0),
                -x.get("final_score", 0),
                -x.get("relevance", x.get("relevance_score", 0)),
                -x.get("is_core_match", False),
                -x.get("matched_theme_count", 0)
            )
        )
        
        return sorted_resources
    
    def _format_resources_by_theme(
        self,
        resources: List[Dict[str, Any]],
        icon: str,
        category_name: str,
        scenario: str = "search",
        state: Any = None
    ) -> List[str]:
        """
        按主题分组展示资源（解决"和"字的并列关系问题）
        实现"类优先原则"：先展示单一主题资源（每类多个），再展示综合性资源
        
        Args:
            resources: 资源列表
            icon: 图标
            category_name: 分类名称
            scenario: 场景类型
            state: 状态对象，用于获取用户原始查询
            
        Returns:
            响应部分列表
        """
        response_parts = []
        
        # 获取用户原始查询，用于提取所有查询主题
        user_input = self._get_state_value(state, "user_input", "")
        
        # 提取查询中的所有主题
        query_themes = []
        if user_input:
            # 简单的主题提取逻辑
            theme_keywords = ["二次函数", "指数函数", "对数函数", "幂函数", "三角函数"]
            for keyword in theme_keywords:
                if keyword in user_input:
                    query_themes.append(keyword)
        
        # 第一步：分离综合性资源和单一主题资源
        comprehensive_resources = []
        single_theme_resources = []
        
        for resource in resources:
            # 检查资源是否与所有查询主题相关
            matched_themes = resource.get("matched_themes", [])
            
            # 如果有查询主题，确保资源至少匹配一个查询主题
            if query_themes:
                # 检查资源是否至少匹配一个查询主题
                has_matching_theme = any(theme in query_themes for theme in matched_themes)
                if not has_matching_theme:
                    # 不匹配任何查询主题，跳过
                    continue
            
            if resource.get("is_comprehensive", False):
                comprehensive_resources.append(resource)
            else:
                single_theme_resources.append(resource)
        
        # 第二步：按主题分组单一主题资源
        theme_resources = {}
        for resource in single_theme_resources:
            matched_themes = resource.get("matched_themes", [])
            if not matched_themes:
                continue
            
            # 只使用查询主题进行分组
            for theme in matched_themes:
                if query_themes and theme not in query_themes:
                    continue  # 跳过非查询主题
                
                if theme not in theme_resources:
                    theme_resources[theme] = []
                if resource not in theme_resources[theme]:
                    theme_resources[theme].append(resource)
        
        # 第三步：先展示所有单一主题资源（类优先原则）
        # 按主题显示资源，让用户看到每类都有多个选择
        for theme in sorted(theme_resources.keys()):
            theme_group = theme_resources[theme]
            response_parts.append(f"\n📌 【{theme}】相关资源（{len(theme_group)}个）：\n")
            for resource in theme_group:
                self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        
        # 第四步：再展示综合性资源（增值需求）
        if comprehensive_resources:
            response_parts.append(f"\n\n⭐ 【综合性资源】同时包含多个查询主题（{len(comprehensive_resources)}个）：\n")
            for resource in comprehensive_resources:
                self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=True, state=state)
        
        return response_parts
    
    def _format_resources_by_domain(
        self,
        resources: List[Dict[str, Any]],
        icon: str,
        category_name: str,
        scenario: str = "search",
        state: Any = None
    ) -> List[str]:
        """
        V10.0：分层展示机制，从"最优解"思维转向"全面性"思维
        
        改进：
        - 明确展示不同级别的资源
        - 保留更多有价值的资源
        - 提供渐进式的资源浏览体验
        """
        response_parts = []
        
        # 先按相关性排序所有资源
        sorted_resources = sorted(
            resources,
            key=lambda x: (
                -x.get('relevance', 0),  # 相关性优先
                -x.get('is_core_match', False),
                -x.get('matched_theme_count', 0)
            )
        )
        
        # 将资源按领域分类（使用V9.0的领域分类）
        domain_resources = {}
        for resource in sorted_resources:
            # 使用V9.0计算的领域，而不是自己分类
            domain = resource.get('domain', '其他')
            if domain not in domain_resources:
                domain_resources[domain] = []
            domain_resources[domain].append(resource)
        
        # 动态确定领域显示顺序：
        # 1. 首先根据用户查询的核心主题确定优先领域
        # 2. 然后按该领域最高相关性资源排序
        query = ""
        if state:
            query = self._get_state_value(state, "user_input", "")
        priority_domains = self._get_priority_domains(query)
        
        domain_max_relevance = {}
        domain_avg_relevance = {}
        for domain, domain_res_list in domain_resources.items():
            if domain_res_list:
                domain_max_relevance[domain] = max(r.get('relevance', 0) for r in domain_res_list)
                domain_avg_relevance[domain] = sum(r.get('relevance', 0) for r in domain_res_list) / len(domain_res_list)
        
        # 排序函数：优先领域 > 最高相关性 > 平均相关性 > 领域名称
        def domain_sort_key(domain):
            priority = -100 if domain in priority_domains else 0
            return (priority, -domain_max_relevance.get(domain, 0), -domain_avg_relevance.get(domain, 0), domain)
        
        # 按优先级排序领域
        domain_order = sorted(
            domain_resources.keys(),
            key=domain_sort_key
        )
        
        # 如果没有资源，使用默认顺序
        if not domain_order:
            domain_order = ["一般函数", "三角函数", "具体函数", "其他"]

        # 按动态排序后的领域顺序显示资源
        for domain in domain_order:
            if domain not in domain_resources or not domain_resources[domain]:
                continue

            # V11.2：为每个领域内的资源按决策中心的优先级层级分类
            priority_resources = {
                4: [],  # 核心主题匹配
                3: [],  # 相关主题匹配
                2: [],  # 扩展主题匹配
                1: [],  # 提及主题匹配
                0: []   # 无匹配
            }
            
            # 分类资源（使用决策中心的priority_level）
            for resource in domain_resources[domain]:
                priority_level = resource.get('priority_level', 0)
                priority_resources[priority_level].append(resource)
            
            # V11.2：显示核心主题匹配资源（优先级4）
            if priority_resources[4]:
                if domain == "一般函数":
                    response_parts.append("\n⭐ 【一般函数】核心主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n⭐ 【三角函数】核心主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n⭐ 【具体函数】核心主题匹配：\n")
                else:
                    response_parts.append(f"\n⭐ 【{domain}】核心主题匹配：\n")
                
                for resource in priority_resources[4]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示相关主题匹配资源（优先级3）
            if priority_resources[3]:
                if domain == "一般函数":
                    response_parts.append("\n📌 【一般函数】相关主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n📌 【三角函数】相关主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n📌 【具体函数】相关主题匹配：\n")
                else:
                    response_parts.append(f"\n📌 【{domain}】相关主题匹配：\n")
                
                for resource in priority_resources[3]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示扩展主题匹配资源（优先级2）
            if priority_resources[2]:
                if domain == "一般函数":
                    response_parts.append("\n📎 【一般函数】扩展主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n📎 【三角函数】扩展主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n📎 【具体函数】扩展主题匹配：\n")
                else:
                    response_parts.append(f"\n📎 【{domain}】扩展主题匹配：\n")
                
                for resource in priority_resources[2]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
            
            # V11.2：显示提及主题匹配资源（优先级1）
            if priority_resources[1]:
                if domain == "一般函数":
                    response_parts.append("\n💡 【一般函数】提及主题匹配：\n")
                elif domain == "三角函数":
                    response_parts.append("\n💡 【三角函数】提及主题匹配：\n")
                elif domain == "具体函数":
                    response_parts.append("\n💡 【具体函数】提及主题匹配：\n")
                else:
                    response_parts.append(f"\n💡 【{domain}】提及主题匹配：\n")
                
                for resource in priority_resources[1]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)
        
        return response_parts
    
    def _format_resource_category(
        self,
        category_name: str,
        resources: List[Dict[str, Any]],
        icon: str,
        scenario: str = "search",
        state: Any = None
    ) -> str:
        """
        格式化资源分类 - 改进版
        增强结果呈现，标注资源匹配的主题信息

        Args:
            category_name: 分类名称
            resources: 资源列表
            icon: 图标
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景

        Returns:
            格式化后的文本
        """
        response_parts = [f"\n【{category_name}】\n"]

        if not resources:
            return "\n".join(response_parts)

        # 过滤掉相似度过低的资源
        filtered_resources = self._filter_by_relevance(resources)

        # V10.0：基于全局综合得分排序
        globally_sorted_resources = self._sort_resources_globally(filtered_resources)
        
        # V10.0：使用用户反馈优化排序
        feedback_optimized_resources = self._optimize_ranking_with_feedback(globally_sorted_resources)
        
        # V11.3：直接使用决策中心的优先级层级进行分类，不再使用动态聚类
        # 按优先级层级分组
        priority_groups = {
            4: [],  # 核心主题匹配
            3: [],  # 相关主题匹配
            2: [],  # 扩展主题匹配
            1: [],  # 提及主题匹配
            0: []   # 无匹配
        }
        
        for resource in feedback_optimized_resources:
            priority_level = resource.get("priority_level", 0)
            priority_groups[priority_level].append(resource)
        
        # 按优先级顺序显示资源
        priority_names = {
            4: "核心主题匹配",
            3: "相关主题匹配",
            2: "扩展主题匹配",
            1: "提及主题匹配",
            0: "其他资源"
        }
        
        priority_icons = {
            4: "⭐",
            3: "📌",
            2: "📎",
            1: "💡",
            0: "📄"
        }
        
        for level in [4, 3, 2, 1, 0]:
            if priority_groups[level]:
                icon_emoji = priority_icons[level]
                category_label = priority_names[level]
                response_parts.append(f"\n{icon_emoji} 【{category_label}】（{len(priority_groups[level])}个）：\n")
                for resource in priority_groups[level][:15]:  # 每个分类最多显示15个资源
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)

        # 如果过滤掉了资源，添加提示
        if len(filtered_resources) < len(resources):
            filtered_count = len(resources) - len(filtered_resources)
            response_parts.append(f"\n💡 已隐藏{filtered_count}条相似度较低的资源")

        return "\n".join(response_parts)

    def _append_resource_info(
        self,
        response_parts: List[str],
        resource: Dict[str, Any],
        icon: str,
        category_name: str,
        scenario: str,
        is_comprehensive: bool = False,
        state: Any = None
    ):
        """
        追加资源信息到响应部分（V8.2改进版）

        Args:
            response_parts: 响应部分列表
            resource: 资源字典
            icon: 图标
            category_name: 分类名称
            scenario: 场景类型
            is_comprehensive: 是否为综合性资源
            state: 状态对象，用于获取用户原始查询
        """
        title = resource.get("title", "未知")
        content = resource.get("content", "")
        relevance = resource.get("relevance", 0)
        source = resource.get("source", "")
        matched_themes = resource.get("matched_themes", [])
        matched_theme_count = resource.get("matched_theme_count", 0)
        
        # V9.0：获取精准匹配信息
        core_theme = resource.get("core_theme")
        related_themes = resource.get("related_themes", [])
        mentioned_themes = resource.get("mentioned_themes", [])
        is_core_match = resource.get("is_core_match", False)
        match_level = resource.get("match_level", "none")
        match_explanation = resource.get("match_explanation", "")
        
        # V11.3：获取多维度评估信息（不使用默认值，直接显示实际值）
        overall_score = resource.get("overall_score", resource.get("relevance", 0))
        # V11.3：不使用默认值，如果值为None则显示0
        resource_quality = resource.get("resource_quality")
        if resource_quality is None:
            resource_quality = 0.0
        content_completeness = resource.get("content_completeness")
        if content_completeness is None:
            content_completeness = 0.0
        teaching_value = resource.get("teaching_value")
        if teaching_value is None:
            teaching_value = 0.0
        comprehensiveness = resource.get("comprehensiveness")
        if comprehensiveness is None:
            comprehensiveness = 0.0

        # 处理内容
        processed_content = self._process_resource_content(
            category_name,
            title,
            content,
            scenario
        )

        # 获取用户原始查询，用于提取所有查询主题
        user_input = ""
        if state:
            user_input = self._get_state_value(state, "user_input", "")
        
        # 提取查询中的所有主题
        query_themes = []
        if user_input:
            # 改进：更全面的主题提取逻辑
            theme_keywords = [
                "二次函数", "指数函数", "对数函数", "幂函数", "三角函数",
                "三角恒等变换", "诱导公式", "函数的单调性", "函数的奇偶性",
                "函数的周期性", "函数的概念", "函数的性质", "函数的应用"
            ]
            for keyword in theme_keywords:
                if keyword in user_input:
                    query_themes.append(keyword)
            
            # 特殊处理：如果用户查询包含"三角恒等变换"，也添加"三角函数"到查询主题
            if "三角恒等变换" in user_input:
                if "三角函数" not in query_themes:
                    query_themes.append("三角函数")
            # 特殊处理：如果用户查询包含具体的三角函数主题，也添加"三角函数"到查询主题
            elif any(trig_theme in user_input for trig_theme in ["诱导公式", "三角恒等"]):
                if "三角函数" not in query_themes:
                    query_themes.append("三角函数")
        
        # V9.0：构建精准主题匹配标签
        theme_tags = ""
        if core_theme:
            # 核心主题匹配
            if matched_theme_count > 1:
                # 多主题匹配，只显示与查询相关的主题
                relevant_themes = [theme for theme in matched_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
                if relevant_themes:
                    theme_tags = f" [匹配主题: {', '.join(relevant_themes)}]"
            else:
                # 单主题匹配，只显示与查询相关的主题
                if not query_themes or core_theme in query_themes or any(qt in core_theme for qt in query_themes):
                    theme_tags = f" [核心主题: {core_theme}]"
        elif related_themes:
            # 相关主题匹配，只显示与查询相关的主题
            relevant_related = [theme for theme in related_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
            if relevant_related:
                theme_tags = f" [相关主题: {relevant_related[0]}]"
        elif mentioned_themes:
            # 提及主题匹配，只显示与查询相关的主题
            relevant_mentioned = [theme for theme in mentioned_themes if not query_themes or theme in query_themes or any(qt in theme for qt in query_themes)]
            if relevant_mentioned:
                theme_tags = f" [提及主题: {relevant_mentioned[0]}]"
        elif matched_theme_count > 1:
            theme_tags = f" [匹配主题: {', '.join(matched_themes)}]"
        elif matched_themes:
            theme_tags = f" [主题: {matched_themes[0]}]"

        # V9.0：核心主题匹配添加特殊标记
        if is_core_match:
            response_parts.append(f"{icon} ⭐ {title}{theme_tags}")
        elif is_comprehensive:
            response_parts.append(f"{icon} 🔥 {title}{theme_tags}")
        else:
            response_parts.append(f"{icon} {title}{theme_tags}")

        response_parts.append(f"   内容: {processed_content}")
        
        # V8.2：显示真实相关性分数
        if is_core_match:
            response_parts.append(f"   相关性: {relevance*100:.1f}% (核心匹配)")
        else:
            response_parts.append(f"   相关性: {relevance*100:.1f}%")
        
        # V10.0：显示多维度评估结果
        response_parts.append(f"   综合得分: {overall_score*100:.1f}%")
        response_parts.append(f"   资源质量: {resource_quality*100:.1f}%")
        response_parts.append(f"   内容完整性: {content_completeness*100:.1f}%")
        response_parts.append(f"   教学价值: {teaching_value*100:.1f}%")
        response_parts.append(f"   综合性: {comprehensiveness*100:.1f}%")
            
        response_parts.append(f"   文件路径: {source}")
        response_parts.append("")
    
    def _filter_by_relevance(self, resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        V10.0：平滑的渐进式展示，替代"悬崖式"截断
        
        改进：
        - 移除40%下跌截断机制
        - 基于分级阈值的平滑过滤
        - 保留更多有价值的资源
        
        Args:
            resources: 资源列表
        
        Returns:
            过滤后的资源列表
        """
        if not resources:
            return []
        
        # 按相关性排序
        sorted_resources = sorted(
            resources,
            key=lambda x: (-
                x.get('relevance', 0),
                -x.get('is_core_match', False),
                -x.get('matched_theme_count', 0)
            )
        )
        
        # 分级展示阈值
        thresholds = {
            'core': 0.8,    # 核心资源
            'high': 0.6,    # 高相关资源
            'medium': 0.4,  # 中等相关资源
            'low': 0.2      # 低相关资源
        }
        
        # 分级过滤
        filtered_resources = []
        level_counts = {
            'core': 0, 'high': 0, 'medium': 0, 'low': 0
        }
        
        # 每个级别的最大展示数量
        max_counts = {
            'core': 10,    # 核心资源最多10个
            'high': 15,    # 高相关资源最多15个
            'medium': 10,  # 中等相关资源最多10个
            'low': 5       # 低相关资源最多5个
        }
        
        for resource in sorted_resources:
            relevance = resource.get('relevance', 0)
            
            # 确定资源级别
            if relevance >= thresholds['core']:
                level = 'core'
            elif relevance >= thresholds['high']:
                level = 'high'
            elif relevance >= thresholds['medium']:
                level = 'medium'
            elif relevance >= thresholds['low']:
                level = 'low'
            else:
                continue  # 低于最低阈值，过滤掉
            
            # 检查该级别的资源数量是否达到上限
            if level_counts[level] < max_counts[level]:
                filtered_resources.append(resource)
                level_counts[level] += 1
        
        return filtered_resources
    
    def _process_resource_content(
        self, 
        category: str, 
        title: str, 
        content: str,
        scenario: str = "search"
    ) -> str:
        """
        处理资源内容
        
        Args:
            category: 资源分类
            title: 资源标题
            content: 原始内容
            scenario: 场景类型，"search"表示资源检索场景，"generation"表示教案生成场景
        
        Returns:
            处理后的内容
        """
        # 习题资源特殊处理
        if category == "习题资源":
            if "【图片题目】" in content:
                # 图片题目，显示文件名
                return "【图片题目】请查看题目文件"
            else:
                # 文字题目，显示完整内容
                return content[:200] + "..." if len(content) > 200 else content
        
        # 课件、课例、GGB只显示文件名
        if category in ["课件资源", "课例资源", "GGB资源"]:
            return "（请查看文件）"
        
        # 教案和教学大纲，根据场景决定是否显示内容
        if category in ["教案资源", "教学大纲"]:
            # 资源检索场景：只显示文件名，不显示内容
            if scenario == "search":
                return "（请查看文件）"
            # 教案生成场景：返回完整内容
            else:
                return content
        
        # 其他资源，生成摘要
        return self.content_processor.generate_summary(content, max_length=150)
    
    def _get_error_response(self, error_msg: str) -> str:
        """
        获取错误响应
        
        Args:
            error_msg: 错误信息
        
        Returns:
            错误响应文本
        """
        return f"抱歉，响应生成过程中出现错误：{error_msg}\n\n请稍后重试或联系管理员。"
    
    def _check_timeout(self) -> bool:
        """
        V33.0改进：检查是否超时
        
        Returns:
            是否超时
        """
        if self.start_time is None:
            return False
        
        elapsed = time.time() - self.start_time
        return elapsed > self.timeout
    
    def _get_timeout_response(self) -> str:
        """
        V33.0改进：获取超时响应（降级方案）
        
        Returns:
            超时响应文本
        """
        return """抱歉，响应生成超时。系统正在努力处理您的请求。

可能的原因：
1. 查询过于复杂，需要更多时间处理
2. 系统负载较高，响应速度较慢

建议：
- 尝试简化您的查询
- 使用更具体的关键词
- 稍后重试

如果您需要帮助，可以尝试：
- 使用更简单的查询方式
- 指定具体的资源类型（如"习题"、"教案"等）
- 限制查询范围（如指定具体的知识点）"""
    
    def _get_fallback_response(self, state: Any) -> str:
        """
        V33.0改进：获取降级响应（当完整响应生成失败时）
        
        Args:
            state: 状态对象
        
        Returns:
            降级响应文本
        """
        # 尝试获取已有的部分响应
        existing_response = self._get_state_value(state, "response", "")
        if existing_response:
            return f"系统响应生成不完整，以下是部分结果：\n\n{existing_response}"
        
        # 尝试获取检索到的资源
        retrieved_resources = self._get_state_value(state, "retrieved_resources", {})
        if retrieved_resources:
            return """系统响应生成不完整，但已找到相关资源。

请尝试：
- 刷新页面重新加载
- 使用更简单的查询方式
- 稍后重试"""
        
        return """抱歉，系统响应生成失败。

请尝试：
- 刷新页面重新加载
- 使用更简单的查询方式
- 稍后重试
- 联系管理员"""
    
    def _get_state_value(self, state: Any, key: str, default: Any = None) -> Any:
        """
        从状态对象中获取值（支持 MathAgentState 对象和字典）
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
            key: 键名
            default: 默认值
        
        Returns:
            对应的值
        """
        if hasattr(state, key):
            return getattr(state, key)
        elif isinstance(state, dict):
            return state.get(key, default)
        else:
            return default


# 向后兼容的函数接口
def response_formatting_node(state) -> Dict[str, Any]:
    """
    响应格式化节点（向后兼容接口）
    
    Args:
        state: 状态对象
    
    Returns:
        包含响应的更新状态
    """
    # 构建响应
    builder = ResponseBuilder()
    response = builder.build(state)
    
    return {
        "response": response,
        "current_step": "response_formatting",
        "error": None,
        "messages": [{"role": "assistant", "content": response}]
    }
