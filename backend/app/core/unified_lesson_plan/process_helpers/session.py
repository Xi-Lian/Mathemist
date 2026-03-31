from .._shared import *


def ensure_session(system, session_id):
    if not session_id:
        session_id = f"lp_{uuid.uuid4().hex[:8]}"
        system.sessions[session_id] = {
            "collected_info": {},
            "lesson_plan": None,
            "conversation_history": [],
            "last_activity": str(time.time()),
            "progress": 0,
        }
        print(f"🆕 创建新会话: {session_id}")
    elif session_id not in system.sessions:
        if system.latest_lesson_plan:
            system.sessions[session_id] = {
                "collected_info": {"topic": system.latest_topic or "教案"},
                "lesson_plan": system.latest_lesson_plan,
                "conversation_history": [],
                "last_activity": str(time.time()),
                "progress": 100,
            }
            print(f"🔄 会话不存在，从最新教案恢复: {session_id}")
        else:
            system.sessions[session_id] = {
                "collected_info": {},
                "lesson_plan": None,
                "conversation_history": [],
                "last_activity": str(time.time()),
                "progress": 0,
            }
            print(f"🆕 会话不存在，创建新会话: {session_id}")
    return session_id, system.sessions[session_id]


def recover_session_from_latest(system):
    if not system.latest_lesson_plan:
        return None, None
    session_id = f"lp_{uuid.uuid4().hex[:8]}"
    system.sessions[session_id] = {
        "collected_info": {"topic": system.latest_topic or "教案"},
        "lesson_plan": system.latest_lesson_plan,
        "conversation_history": [],
        "last_activity": str(time.time()),
        "progress": 100,
    }
    return session_id, system.sessions[session_id]
