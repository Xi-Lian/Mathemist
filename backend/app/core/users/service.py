"""
服务实现。
"""

from ._shared import *
from .methods.init import _InitMixin
from .methods.initialize_data_files import _InitializeDataFilesMixin
from .methods.load_users import _LoadUsersMixin
from .methods.save_users import _SaveUsersMixin
from .methods.load_history import _LoadHistoryMixin
from .methods.save_history import _SaveHistoryMixin
from .methods.create_user import _CreateUserMixin
from .methods.get_user import _GetUserMixin
from .methods.get_user_by_email import _GetUserByEmailMixin
from .methods.update_user_preferences import _UpdateUserPreferencesMixin
from .methods.create_lesson_plan_history import _CreateLessonPlanHistoryMixin
from .methods.update_lesson_plan_history import _UpdateLessonPlanHistoryMixin
from .methods.get_lesson_plan_history import _GetLessonPlanHistoryMixin
from .methods.get_user_lesson_plan_history import _GetUserLessonPlanHistoryMixin
from .methods.delete_lesson_plan_history import _DeleteLessonPlanHistoryMixin
from .methods.search_lesson_plan_history import _SearchLessonPlanHistoryMixin

class UserSystem(_InitMixin, _InitializeDataFilesMixin, _LoadUsersMixin, _SaveUsersMixin, _LoadHistoryMixin, _SaveHistoryMixin, _CreateUserMixin, _GetUserMixin, _GetUserByEmailMixin, _UpdateUserPreferencesMixin, _CreateLessonPlanHistoryMixin, _UpdateLessonPlanHistoryMixin, _GetLessonPlanHistoryMixin, _GetUserLessonPlanHistoryMixin, _DeleteLessonPlanHistoryMixin, _SearchLessonPlanHistoryMixin):
    """用户系统管理器"""


user_system = UserSystem()

def create_user(username: str, email: str) -> User:
    """创建新用户"""
    return user_system.create_user(username, email)


def get_user(user_id: str) -> Optional[User]:
    """获取用户信息"""
    return user_system.get_user(user_id)


def get_user_by_email(email: str) -> Optional[User]:
    """通过邮箱获取用户"""
    return user_system.get_user_by_email(email)


def update_user_preferences(user_id: str, preferences: Dict[str, Any]) -> Optional[User]:
    """更新用户偏好"""
    return user_system.update_user_preferences(user_id, preferences)


def create_lesson_plan_history(
    user_id: str,
    topic: str,
    **kwargs
) -> LessonPlanHistory:
    """创建备课历史"""
    return user_system.create_lesson_plan_history(user_id, topic, **kwargs)


def update_lesson_plan_history(history_id: str, **kwargs) -> Optional[LessonPlanHistory]:
    """更新备课历史"""
    return user_system.update_lesson_plan_history(history_id, **kwargs)


def get_lesson_plan_history(history_id: str) -> Optional[LessonPlanHistory]:
    """获取备课历史"""
    return user_system.get_lesson_plan_history(history_id)


def get_user_lesson_plan_history(
    user_id: str,
    **kwargs
) -> List[LessonPlanHistory]:
    """获取用户备课历史列表"""
    return user_system.get_user_lesson_plan_history(user_id, **kwargs)


def delete_lesson_plan_history(history_id: str) -> bool:
    """删除备课历史"""
    return user_system.delete_lesson_plan_history(history_id)


def search_lesson_plan_history(
    user_id: str,
    keyword: str,
    **kwargs
) -> List[LessonPlanHistory]:
    """搜索备课历史"""
    return user_system.search_lesson_plan_history(user_id, keyword, **kwargs)
