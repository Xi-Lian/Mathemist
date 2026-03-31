from .._shared import *


class _CreateUserMixin:
    def create_user(self, username: str, email: str) -> User:
        """
        创建新用户
        
        Args:
            username: 用户名
            email: 邮箱
        
        Returns:
            创建的用户对象
        """
        users = self._load_users()
        
        # 检查邮箱是否已存在
        for user_data in users.values():
            if user_data['email'] == email:
                raise ValueError(f"邮箱 {email} 已被使用")
        
        user_id = str(uuid.uuid4())
        user = User(
            user_id=user_id,
            username=username,
            email=email
        )
        
        users[user_id] = user.to_dict()
        self._save_users(users)
        
        print(f"✅ 用户创建成功: {username} ({email})")
        return user
