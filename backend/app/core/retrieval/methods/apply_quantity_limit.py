from .._shared import *


class _ApplyQuantityLimitMixin:
    def _apply_quantity_limit(self, classified: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """
        V33.0: 应用数量限制
        
        Args:
            classified: 分类后的资源
            limit: 数量限制
        
        Returns:
            限制后的资源
        """
        total_count = sum(len(resources) for resources in classified.values() if isinstance(resources, list))
        
        if total_count <= limit:
            print(f"   📊 V33.0数量限制: 资源不足（{total_count}个），返回所有资源")
            # V96.0改进：添加资源不足的提示
            # 向classified中添加资源不足的提示信息
            if 'message' not in classified:
                classified['message'] = []
            classified['message'].append(f"资源不足，已返回所有可用资源（共{total_count}个）")
            return classified
        
        all_resources = []
        for category in classified:
            if isinstance(classified[category], list):
                for resource in classified[category]:
                    resource['_category'] = category
                    all_resources.append(resource)
        
        all_resources.sort(key=lambda x: -x.get('relevance', 0))
        
        limited_resources = all_resources[:limit]
        
        new_classified = {key: [] for key in classified.keys()}
        for resource in limited_resources:
            category = resource.pop('_category', 'general_resources')
            if category in new_classified:
                new_classified[category].append(resource)
        
        print(f"   📊 V33.0数量限制: 原始{total_count}个 -> 限制后{len(limited_resources)}个")
        
        return new_classified
