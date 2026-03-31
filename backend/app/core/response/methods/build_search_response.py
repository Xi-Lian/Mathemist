from .._shared import *


class _BuildSearchResponseMixin:
    def _build_search_response(self, state: Any) -> str:
        """
        构建资源搜索响应
        
        Args:
            state: 状态对象（可以是 MathAgentState 对象或字典）
        
        Returns:
            搜索响应文本
        """
        # 对于搜索意图，只显示检索到的资源，不显示生成的内容
        # 确保主次分明，避免生成内容干扰用户对检索结果的判断
        return self._format_resources(state, scenario="search")
