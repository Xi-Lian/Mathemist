from .._shared import *
from ..ai_rerank_helpers import apply_ai_screen_and_rerank


class _ApplyAiRerankMixin:
    def _apply_ai_rerank_stage(
        self,
        classified_resources: Dict[str, Any],
        query: str,
        intent: str,
        resource_types: List[str],
        core_theme: str,
    ) -> Dict[str, Any]:
        mode = getattr(self, "retrieval_mode", "ai_first")
        max_calls = getattr(self, "retrieval_ai_max_calls", 2)

        if mode == "legacy":
            classified_resources["_ai_decision"] = {
                "enabled": False,
                "mode": mode,
                "applied": False,
                "reason": "legacy_mode",
                "max_calls": max_calls,
            }
            return classified_resources

        ai_result = apply_ai_screen_and_rerank(
            classified_resources,
            query,
            intent,
            resource_types or [],
            core_theme or "",
            max_calls,
        )

        if not ai_result.get("ok"):
            print(f"🤖 AI筛选未生效，原因: {ai_result.get('reason', 'unknown')}，保持旧结果")
            classified_resources["_ai_decision"] = {
                "enabled": True,
                "mode": mode,
                "applied": False,
                "reason": ai_result.get("reason", "unknown"),
                "call_count": ai_result.get("call_count", 0),
                "max_calls": max_calls,
            }
            return classified_resources

        print(
            f"🤖 AI筛选成功: mode={mode}, calls={ai_result.get('call_count', 1)}, selected={ai_result.get('selected_count', 0)}"
        )

        final_result = ai_result.get("result", classified_resources)
        final_result["_ai_decision"] = {
            "enabled": True,
            "mode": mode,
            "applied": True,
            "reason": ai_result.get("reason", ""),
            "call_count": ai_result.get("call_count", 1),
            "selected_count": ai_result.get("selected_count", 0),
            "max_calls": max_calls,
        }
        return final_result
