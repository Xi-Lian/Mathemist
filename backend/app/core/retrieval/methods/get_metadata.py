from .._shared import *


class _GetMetadataMixin:
    def _get_metadata(self, results: Dict[str, Any], index: int) -> Dict[str, Any]:
        """
        安全地获取元数据
        
        Args:
            results: 查询结果
            index: 索引
        
        Returns:
            元数据字典
        """
        if results.get("metadatas") and results["metadatas"][0]:
            if index < len(results["metadatas"][0]):
                return results["metadatas"][0][index]
        return {}
