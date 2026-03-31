from .._shared import *


class _CheckVectorDbExistsMixin:
    def _check_vector_db_exists(self) -> bool:
        """
        检查向量数据库是否存在
        
        Returns:
            是否存在
        """
        return self.vector_db_builder.check_database_exists()
