from .._shared import *


class _CleanExpiredSessionsMixin:
    def _clean_expired_sessions(self):
        """
        清理过期会话
        """
        import time
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            last_activity = session.get("last_activity")
            if last_activity:
                # 尝试将UUID转换为时间戳（简化处理）
                # 实际项目中应该使用真实的时间戳
                if len(last_activity) == 36:  # UUID格式
                    # 这里简化处理，实际应该存储真实的时间戳
                    continue
                try:
                    last_activity_time = float(last_activity)
                    if current_time - last_activity_time > self.session_timeout:
                        expired_sessions.append(session_id)
                except:
                    pass
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
            print(f"🗑️ 清理过期会话: {session_id}")
