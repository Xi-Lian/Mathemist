from .._shared import *


class _ParseQueryGradeMixin:
    def _parse_query_grade(self, query_grade: str) -> int:
        """
        解析查询中的年级要求
        
        Args:
            query_grade: 年级字符串
            
        Returns:
            年级级别
        """
        if not query_grade:
            return 0
        
        query_lower = query_grade.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    return self._grade_to_level(grade_key)
        
        # 检查教材册别
        for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
            if book_key.lower() in query_lower:
                return book_info['grade_level']
        
        return 0
