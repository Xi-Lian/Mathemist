from .._shared import *


class _IsParallelQueryMixin:
    def _is_parallel_query(self, state: Any) -> bool:
        """
        判断是否为多主题并列查询（包含"和"、"与"、"及"等并列词）
        
        Args:
            state: 状态对象
            
        Returns:
            是否为多主题并列查询
        """
        user_input = self._get_state_value(state, "user_input", "")
        if not user_input:
            return False
        
        # 并列词列表
        parallel_keywords = ["和", "与", "及", "以及", "还有", "加上"]
        
        # 检查是否包含并列词
        for keyword in parallel_keywords:
            if keyword in user_input:
                print(f"🔀 检测到并列词 '{keyword}'，判断为多主题并列查询")
                return True
        
        return False
