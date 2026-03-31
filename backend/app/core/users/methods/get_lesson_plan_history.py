from .._shared import *


class _GetLessonPlanHistoryMixin:
    def get_lesson_plan_history(self, history_id: str) -> Optional[LessonPlanHistory]:
        """
        获取单个备课历史记录
        
        Args:
            history_id: 历史记录ID
        
        Returns:
            历史记录对象
        """
        history_list = self._load_history()
        for history_data in history_list:
            if history_data['history_id'] == history_id:
                return LessonPlanHistory.from_dict(history_data)
        return None
