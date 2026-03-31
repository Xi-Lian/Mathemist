from .._shared import *


class _ExtractQuestionTypeMixin:
    def _extract_question_type(self, query: str) -> str:
        """
        V45.0改进：从查询中提取题目类型
        
        Args:
            query: 用户查询
        
        Returns:
            题目类型字符串
        """
        # 使用新的多维度提取方法
        conditions = self._extract_query_conditions(query)
        return conditions['question_type']
