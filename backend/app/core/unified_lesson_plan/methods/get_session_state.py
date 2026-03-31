from .._shared import *


class _GetSessionStateMixin:
    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话状态"""
        if session_id not in self.sessions:
            return None
        # 更新会话活动时间
        self._update_session_activity(session_id)
        return self.sessions[session_id]
