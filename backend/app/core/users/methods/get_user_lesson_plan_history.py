from .._shared import *


class _GetUserLessonPlanHistoryMixin:
    def get_user_lesson_plan_history(
        self,
        user_id: str,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[LessonPlanHistory]:
        """
        获取用户的备课历史列表
        
        Args:
            user_id: 用户ID
            status: 状态过滤（可选）
            limit: 返回数量限制
            offset: 偏移量
        
        Returns:
            历史记录列表
        """
        history_list = self._load_history()
        
        # 过滤用户历史
        user_history = [
            h for h in history_list
            if h['user_id'] == user_id
        ]
        
        # 状态过滤
        if status:
            user_history = [
                h for h in user_history
                if h['status'] == status
            ]
        
        # 按更新时间倒序排列
        user_history.sort(
            key=lambda x: x['updated_at'],
            reverse=True
        )
        
        # 分页
        user_history = user_history[offset:offset + limit]
        
        return [LessonPlanHistory.from_dict(h) for h in user_history]
