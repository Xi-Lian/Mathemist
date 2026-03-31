from .._shared import *


class _SearchLessonPlanHistoryMixin:
    def search_lesson_plan_history(
        self,
        user_id: str,
        keyword: str,
        limit: int = 50
    ) -> List[LessonPlanHistory]:
        """
        搜索备课历史
        
        Args:
            user_id: 用户ID
            keyword: 搜索关键词
            limit: 返回数量限制
        
        Returns:
            匹配的历史记录列表
        """
        history_list = self._load_history()
        
        keyword = keyword.lower()
        results = []
        
        for history_data in history_list:
            if history_data['user_id'] != user_id:
                continue
            
            # 在多个字段中搜索
            search_text = ' '.join([
                str(history_data.get('topic', '')),
                str(history_data.get('chapter', '')),
                str(history_data.get('textbook', '')),
                str(history_data.get('notes', '')),
                ' '.join(history_data.get('tags', []))
            ]).lower()
            
            if keyword in search_text:
                results.append(history_data)
        
        # 按更新时间倒序排列
        results.sort(
            key=lambda x: x['updated_at'],
            reverse=True
        )
        
        results = results[:limit]
        
        return [LessonPlanHistory.from_dict(h) for h in results]
