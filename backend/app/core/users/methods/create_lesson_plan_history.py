from .._shared import *


class _CreateLessonPlanHistoryMixin:
    def create_lesson_plan_history(
        self,
        user_id: str,
        topic: str,
        chapter: Optional[str] = None,
        textbook: Optional[str] = None,
        teaching_goals: Optional[str] = None,
        teaching_framework: Optional[str] = None,
        lesson_plan_content: Optional[str] = None,
        tags: Optional[List[str]] = None,
        notes: Optional[str] = None
    ) -> LessonPlanHistory:
        """
        创建备课历史记录
        
        Args:
            user_id: 用户ID
            topic: 课题
            chapter: 章节
            textbook: 教材
            teaching_goals: 教学目标
            teaching_framework: 教学框架
            lesson_plan_content: 教案内容
            tags: 标签列表
            notes: 备注
        
        Returns:
            创建的历史记录对象
        """
        history_id = str(uuid.uuid4())
        history = LessonPlanHistory(
            history_id=history_id,
            user_id=user_id,
            topic=topic,
            chapter=chapter,
            textbook=textbook,
            teaching_goals=teaching_goals,
            teaching_framework=teaching_framework,
            lesson_plan_content=lesson_plan_content,
            status=LessonPlanStatus.DRAFT.value,
            tags=tags or [],
            notes=notes
        )
        
        history_list = self._load_history()
        history_list.append(history.to_dict())
        self._save_history(history_list)
        
        print(f"✅ 备课历史创建成功: {topic}")
        return history
