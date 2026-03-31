from .._shared import *


class _UpdateSessionActivityMixin:
    def _update_session_activity(self, session_id: str):
        """
        更新会话活动时间
        
        Args:
            session_id: 会话ID
        """
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = str(time.time())
            print(f"⏰ 更新会话活动时间: {session_id}")
