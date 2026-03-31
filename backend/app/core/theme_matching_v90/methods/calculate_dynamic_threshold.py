from .._shared import *


class _CalculateDynamicThresholdMixin:
    def _calculate_dynamic_threshold(self, query: str, core_theme_count: int) -> float:
        """
        V9.2：计算动态阈值
        
        根据查询明确度和核心主题数量自动调整阈值
        
        Args:
            query: 用户查询
            core_theme_count: 核心主题数量
        
        Returns:
            float: 动态调整后的阈值
        """
        # 基础阈值
        threshold = self.base_related_theme_threshold
        
        # 根据核心主题数量调整
        if core_theme_count == 0:
            # 没有核心主题，降低阈值以展示更多相关内容
            threshold -= 0.1
        elif core_theme_count >= 3:
            # 核心主题较多，提高阈值以保证质量
            threshold += 0.1
        
        # 根据查询长度判断明确度
        query_length = len(query)
        if query_length >= 10:
            # 查询较长，比较明确，提高阈值
            threshold += 0.05
        elif query_length <= 4:
            # 查询较短，比较泛化，降低阈值
            threshold -= 0.05
        
        # 确保阈值在合理范围内
        threshold = max(0.3, min(0.7, threshold))
        
        return threshold
