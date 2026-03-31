from .._shared import *


class _GetImprovementSuggestionsMixin:
    def get_improvement_suggestions(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取改进建议"""
        suggestions = self.feedback_data["improvement_suggestions"]
        return suggestions[-limit:] if limit > 0 else suggestions
