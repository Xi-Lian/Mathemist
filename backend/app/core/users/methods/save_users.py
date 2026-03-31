from .._shared import *


class _SaveUsersMixin:
    def _save_users(self, users: Dict[str, Dict[str, Any]]):
        """保存用户数据"""
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
