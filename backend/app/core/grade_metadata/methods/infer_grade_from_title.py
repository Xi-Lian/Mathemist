from .._shared import *


class _InferGradeFromTitleMixin:
    def infer_grade_from_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        从标题推断年级信息
        
        Args:
            title: 资源标题
            
        Returns:
            年级信息字典
        """
        if not title:
            return None
        
        title_lower = title.lower()
        
        # 检查年级关键词
        for grade_key, keywords in self.GRADE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in title_lower:
                    grade_level = self._grade_to_level(grade_key)
                    return {
                        'grade': grade_key,
                        'grade_level': grade_level,
                        'inference_source': 'title',
                        'confidence': 0.75
                    }
        
        return None
