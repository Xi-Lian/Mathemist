from .._shared import *


class _CalculateWeightFactorMixin:
    def _calculate_weight_factor(self, theme: str, lesson_title: str, lesson_content: str, query_themes: List[str] = None, metadata: Dict[str, Any] = None) -> float:
        """
        V9.2：计算综合权重因子 - 改进版
        
        使用加权平均替代简单相乘，避免分数衰减过快
        
        改进：
        - 如果排除词因子为0.0，直接返回0.0，过滤掉不相关的资源
        - V27.0：添加metadata参数，支持路径冲突检测
        
        Args:
            theme: 当前主题
            lesson_title: 教案标题
            lesson_content: 教案内容
            query_themes: 查询的主题列表，用于过滤与其他查询主题相关的排除词
            metadata: 资源元数据，包含source_file等信息
        
        Returns:
            float: 综合权重因子 (0.0-1.0)
        """
        # 计算各个因子
        exclusion_factor = self._calculate_exclusion_factor(theme, lesson_title, lesson_content, query_themes, metadata)
        
        # 如果排除词因子为0.0，直接返回0.0，过滤掉不相关的资源
        if exclusion_factor == 0.0:
            return 0.0
        
        domain_factor = self._calculate_domain_distance_factor(theme, lesson_title, lesson_content)
        direction_factor = self._calculate_direction_factor(theme, lesson_title, lesson_content)
        
        # 使用加权平均计算综合因子
        weight_factor = (
            self.weight_factors["exclusion"] * exclusion_factor +
            self.weight_factors["domain"] * domain_factor +
            self.weight_factors["direction"] * direction_factor
        )
        
        return weight_factor
