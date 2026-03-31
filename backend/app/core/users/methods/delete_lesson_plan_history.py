from .._shared import *


class _DeleteLessonPlanHistoryMixin:
    def delete_lesson_plan_history(self, history_id: str) -> bool:
        """
        删除备课历史记录
        
        Args:
            history_id: 历史记录ID
        
        Returns:
            是否删除成功
        """
        history_list = self._load_history()
        original_length = len(history_list)
        
        history_list = [
            h for h in history_list
            if h['history_id'] != history_id
        ]
        
        if len(history_list) < original_length:
            self._save_history(history_list)
            print(f"✅ 备课历史删除成功")
            return True
        
        return False
