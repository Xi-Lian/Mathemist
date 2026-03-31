from .._shared import *
from ..process_helpers.export_flow import (
    handle_export_request,
    handle_format_selection_reply,
    handle_view_full_lesson_plan,
)
from ..process_helpers.generation_flow import handle_generation_flow, prepare_generation_turn
from ..process_helpers.intent_flow import (
    handle_revision_request,
    is_direct_generate_request,
    should_reject_resource_request,
)
from ..process_helpers.session import ensure_session


class _ProcessLessonPlanRequestMixin:
    def process_lesson_plan_request(
        self,
        user_input: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        处理教案生成请求 - 统一入口
        """
        result = handle_view_full_lesson_plan(self, user_input, session_id)
        if result is not None:
            return result

        result = handle_export_request(self, user_input, session_id)
        if result is not None:
            return result

        result = handle_format_selection_reply(self, user_input, session_id)
        if result is not None:
            return result

        result, session_id = handle_revision_request(self, user_input, session_id)
        if result is not None:
            return result

        session_id, session = ensure_session(self, session_id)
        if should_reject_resource_request(session, user_input):
            print("⚠️ 检测到资源获取指令词，拒绝生成教案")
            return {
                "status": "error",
                "message": "您使用了资源获取指令词（如'推送'、'找'、'推荐'等），系统将为您检索相关资源，而不是生成新的教案。",
                "session_id": session_id,
            }

        result = prepare_generation_turn(self, user_input, session_id, session)
        if result is not None:
            return result

        if is_direct_generate_request(user_input):
            print("🚀 用户要求直接生成教案，跳过引导")
            if "topic" not in session["collected_info"] or not session["collected_info"]["topic"]:
                session["collected_info"]["topic"] = user_input
            return self._generate_complete_lesson_plan(session_id, session)

        return handle_generation_flow(self, user_input, session_id, session)
