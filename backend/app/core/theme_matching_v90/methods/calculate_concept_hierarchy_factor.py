from .._shared import *


class _CalculateConceptHierarchyFactorMixin:
    def _calculate_concept_hierarchy_factor(self, query_theme: str, lesson_theme: str) -> float:
        """
        V10.0：计算概念层级关系因子
        
        Args:
            query_theme: 查询主题
            lesson_theme: 教案主题
            
        Returns:
            层级关系因子 (0.0-1.0)
        """
        # 完全匹配
        if query_theme == lesson_theme:
            return 1.0
        
        # 检查是否为子概念
        if query_theme in self.concept_hierarchy:
            if lesson_theme in self.concept_hierarchy[query_theme].get("子概念", []):
                return 0.9  # 子概念匹配
        
        # 检查是否为父概念
        for parent, info in self.concept_hierarchy.items():
            if query_theme in info.get("子概念", []) and parent == lesson_theme:
                return 0.7  # 父概念匹配
        
        # 检查是否为相关概念
        if query_theme in self.concept_hierarchy:
            if lesson_theme in self.concept_hierarchy[query_theme].get("相关概念", []):
                return 0.6  # 相关概念匹配
        
        # 无层级关系
        return 0.5
