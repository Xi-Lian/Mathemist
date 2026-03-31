from .._shared import *


class _GenerateDynamicCategoriesMixin:
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
