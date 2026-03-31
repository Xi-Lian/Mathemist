from .._shared import *


class _FilterByRelevanceMixin:
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
