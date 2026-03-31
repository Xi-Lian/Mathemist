from .._shared import *


class _GetDistanceMixin:
    def _get_distance(self, results: Dict[str, Any], index: int) -> float:
        """
        安全地获取距离
        
        Args:
            results: 查询结果
            index: 索引
        
        Returns:
            距离值
        """
        if results.get("distances") and results["distances"][0]:
            if index < len(results["distances"][0]):
                return results["distances"][0][index]
        return 0.0
