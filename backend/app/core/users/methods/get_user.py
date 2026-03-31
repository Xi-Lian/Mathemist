from .._shared import *


class _GetUserMixin:
    def get_user(self, user_id: str) -> Optional[User]:
        """
        获取用户信息
        
        Args:
            user_id: 用户ID
        
        Returns:
            用户对象，如果不存在则返回None
        """
        users = self._load_users()
        if user_id in users:
            return User.from_dict(users[user_id])
        return None
