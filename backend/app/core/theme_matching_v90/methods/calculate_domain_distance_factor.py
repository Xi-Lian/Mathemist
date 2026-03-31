from .._shared import *


class _CalculateDomainDistanceFactorMixin:
    def _calculate_domain_distance_factor(self, theme: str, lesson_title: str, lesson_content: str) -> float:
        """
        V9.1：计算领域距离因子
        
        领域距离定义：
        - 距离0：同一具体主题，因子1.0
        - 距离1：同一分支的不同具体主题，因子0.8
        - 距离2：同一大类下的不同分支，因子0.5
        - 距离3：不同大类，因子0.2
        
        用于降低跨领域推荐的相关性分数
        """
        # 提取教案的主题
        lesson_theme = self._extract_lesson_theme(lesson_title, lesson_content)
        
        if not lesson_theme:
            return 1.0  # 无法确定主题，不降低分数
        
        # 查找领域距离
        distance = self.domain_distance.get((theme, lesson_theme))
        
        if distance is None:
            return 1.0  # 没有定义距离，不降低分数
        
        # 根据距离返回因子
        distance_factors = {
            0: 1.0,
            1: 0.8,
            2: 0.5,
            3: 0.2
        }
        
        return distance_factors.get(distance, 1.0)
