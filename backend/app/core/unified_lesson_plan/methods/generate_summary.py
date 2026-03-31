from .._shared import *


class _GenerateSummaryMixin:
    def _generate_summary(self, lesson_plan_content: str) -> str:
        """
        生成结构化的教案摘要（现在返回完整内容，不再截断）
        
        Args:
            lesson_plan_content: 完整的教案内容
        
        Returns:
            完整的教案内容（不再截断）
        """
        # 直接返回完整教案内容，不再进行截断
        # 确保用户能够看到完整的教案
        return lesson_plan_content
