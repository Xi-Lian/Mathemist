from .._shared import *


class _AppendResourceInfoMixin:
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
