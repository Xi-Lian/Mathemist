from .._shared import *


class _FormatResourceCategoryMixin:
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
                for resource in priority_groups[level][:self.max_display_per_group]:
                    self._append_resource_info(response_parts, resource, icon, category_name, scenario, is_comprehensive=False, state=state)

        # 如果过滤掉了资源，添加提示
        if len(filtered_resources) < len(resources):
            filtered_count = len(resources) - len(filtered_resources)
            response_parts.append(f"\n💡 已隐藏{filtered_count}条相似度较低的资源")

        return "\n".join(response_parts)
