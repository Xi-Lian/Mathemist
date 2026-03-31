from .._shared import *


class _ExtractGradeInfoMixin:
    def _extract_grade_info(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 从用户输入中提取年级信息
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            年级信息字典
        """
        # V52.0改进：优先匹配更具体的年级（高三、高二、高一），避免误匹配
        # 定义优先级顺序：高三 > 高二 > 高一 > 学期
        priority_order = ['高三', '高二', '高一', '高一上学期', '高一下学期', '高二上学期', '高二下学期']
        
        for grade in priority_order:
            if grade in self.V33_GRADE_PATTERNS:
                keywords = self.V33_GRADE_PATTERNS[grade]
                for keyword in keywords:
                    if keyword in user_input:
                        return {
                            "grade": grade,
                            "grade_keywords_matched": keyword
                        }
        
        return None
