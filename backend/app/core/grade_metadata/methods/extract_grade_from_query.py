from .._shared import *


class _ExtractGradeFromQueryMixin:
    def extract_grade_from_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        从查询中提取年级信息
        
        Args:
            query: 用户查询
            
        Returns:
            年级信息字典，包含grade、grade_level等字段
        """
        if not query:
            return None
        
        query_lower = query.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'query',
                        'confidence': 0.8
                    }
        
        # 检查教材册别
        for book_key, book_info in self.CHAPTER_TO_GRADE_MAPPING.items():
            if book_key.lower() in query_lower:
                return {
                    'grade': book_info['grade'],
                    'grade_level': book_info['grade_level'],
                    'textbook_volume': book_key,
                    'inference_source': 'query',
                    'confidence': 0.9
                }
        
        return None
