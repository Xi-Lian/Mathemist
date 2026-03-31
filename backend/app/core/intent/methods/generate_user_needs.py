from .._shared import *


class _GenerateUserNeedsMixin:
    def _generate_user_needs(self, user_input: str, resource_types: List[str]) -> str:
        """
        生成用户需求描述
        
        Args:
            user_input: 用户输入
            resource_types: 资源类型列表
        
        Returns:
            用户需求描述
        """
        if resource_types:
            return f"用户想要查找{', '.join(resource_types)}相关的资源"
        else:
            return "用户想要查找相关的教学资源"
