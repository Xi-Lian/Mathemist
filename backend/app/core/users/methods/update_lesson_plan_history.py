from .._shared import *


class _UpdateLessonPlanHistoryMixin:
    def update_lesson_plan_history(
        self,
        history_id: str,
        **kwargs
    ) -> Optional[LessonPlanHistory]:
        """
        更新备课历史记录
        
        Args:
            history_id: 历史记录ID
            **kwargs: 要更新的字段
        
        Returns:
            更新后的历史记录对象
        """
        history_list = self._load_history()
        
        for i, history_data in enumerate(history_list):
            if history_data['history_id'] == history_id:
                # 更新字段
                for key, value in kwargs.items():
                    if key in history_data:
                        history_data[key] = value
                
                history_data['updated_at'] = datetime.now().isoformat()
                
                self._save_history(history_list)
                return LessonPlanHistory.from_dict(history_data)
        
        return None
