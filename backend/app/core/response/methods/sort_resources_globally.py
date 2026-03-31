from .._shared import *


class _SortResourcesGloballyMixin:
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
