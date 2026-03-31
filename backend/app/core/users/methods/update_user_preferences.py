from .._shared import *


class _UpdateUserPreferencesMixin:
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Optional[User]:
        """
        更新用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置字典
        
        Returns:
            更新后的用户对象
        """
        users = self._load_users()
        if user_id not in users:
            return None
        
        users[user_id]['preferences'].update(preferences)
        self._save_users(users)
        
        return User.from_dict(users[user_id])
