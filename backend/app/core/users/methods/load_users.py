from .._shared import *


class _LoadUsersMixin:
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """加载用户数据"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            return json.load(f)
