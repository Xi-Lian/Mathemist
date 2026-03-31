from .._shared import *


class _GetUserByEmailMixin:
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        通过邮箱获取用户
        
        Args:
            email: 邮箱
        
        Returns:
            用户对象，如果不存在则返回None
        """
        users = self._load_users()
        for user_data in users.values():
            if user_data['email'] == email:
                return User.from_dict(user_data)
        return None
