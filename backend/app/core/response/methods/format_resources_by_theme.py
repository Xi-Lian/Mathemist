from .._shared import *


class _FormatResourcesByThemeMixin:
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
