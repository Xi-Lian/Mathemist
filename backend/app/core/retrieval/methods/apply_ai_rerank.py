import builtins as _builtins
import logging

from .._shared import *
from ..ai_rerank_helpers import apply_ai_screen_and_rerank

_log = logging.getLogger(__name__)


class _ApplyAiRerankMixin:
    def _apply_ai_rerank_stage(
        self,
        classified_resources: Dict[str, Any],
        query: str,
        intent: str,
        resource_types: List[str],
        core_theme: str,
    ) -> Dict[str, Any]:
        _log.warning(
            f"[方案A调试] _apply_ai_rerank_stage 被调用: "
            f"resource_types={resource_types}, core_theme={core_theme}"
        )
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

        # ── 方案A：习题检索跳过 AI 筛选 ──
        exercise_only = (
            isinstance(resource_types, list)
            and len(resource_types) == 1
            and resource_types[0] in ("exercise", "习题", "练习")
        )
        has_exercise = any(
            isinstance(r, dict) and r.get("resource_type") in ("exercise", "习题")
            for resources in classified_resources.values()
            if isinstance(resources, list)
            for r in resources
        )
        
        # V41.7修复：GGB资源跳过AI重排序，因为GGB资源的匹配主要依赖关键词匹配（标题、教学用途等）
        # AI重排序可能过于严格，过滤掉符合条件的GGB资源
        # V41.9注释：已添加teaching_use字段到候选payload，可以尝试启用AI重排序
        # V41.10修复：只要资源类型列表中包含GGB相关类型，就使用宽松的AI重排序策略
        has_ggb_type = any(
            isinstance(rt, str) and 'ggb' in rt.lower()
            for rt in (resource_types or [])
        )
        has_ggb = any(
            isinstance(r, dict) and r.get("resource_type") and 'ggb' in r.get("resource_type").lower()
            for resources in classified_resources.values()
            if isinstance(resources, list)
            for r in resources
        )

        _log.warning(
            f"[方案A调试] exercise_only={exercise_only}, has_exercise={has_exercise}, "
            f"has_ggb_type={has_ggb_type}, has_ggb={has_ggb}, mode={mode}"
        )
        if exercise_only or has_exercise:
            skip_reason = "exercise_skip" if (exercise_only or has_exercise) else "ggb_skip"
            _log.warning(f"[方案A] AI筛选已跳过: resource_types={resource_types}, reason={skip_reason}")
            classified_resources["_ai_decision"] = {
                "enabled": False,
                "mode": mode,
                "applied": False,
                "reason": skip_reason,
                "max_calls": max_calls,
            }
            return classified_resources
        # ── 方案A 结束 ──

        # 保存原始结果用于回退
        original_classified = dict(classified_resources)
        total_original = sum(len(v) for v in original_classified.values() if isinstance(v, list))
        _log.warning(f"[GGB保护调试] 调用apply_ai_screen_and_rerank前: total_original={total_original}, has_ggb_type={has_ggb_type}, has_ggb={has_ggb}")

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

        # 检查是否是GGB查询且AI过滤过多，如果是则回退到原始结果
        total_after_ai = sum(len(v) for v in ai_result.get("result", {}).values() if isinstance(v, list))
        _log.warning(f"[GGB保护调试] has_ggb_type={has_ggb_type}, has_ggb={has_ggb}, total_original={total_original}, total_after_ai={total_after_ai}, threshold={total_original * 0.5 if total_original > 10 else 'N/A'}")
        if (has_ggb_type or has_ggb) and total_original > 10 and total_after_ai < total_original * 0.5:
            _log.warning(f"[GGB保护] AI过滤过多（{total_after_ai}/{total_original}），回退到原始语义门控结果")
            original_classified["_ai_decision"] = {
                "enabled": True,
                "mode": mode,
                "applied": False,
                "reason": "ggb_fallback_too_many_filtered",
                "call_count": ai_result.get("call_count", 1),
                "original_count": total_original,
                "ai_selected_count": total_after_ai,
                "max_calls": max_calls,
            }
            return original_classified

        print(
            f"🤖 AI筛选成功: mode={mode}, calls={ai_result.get('call_count', 1)}, selected={total_after_ai}/{total_original}"
        )

        final_result = ai_result.get("result", classified_resources)
        final_result["_ai_decision"] = {
            "enabled": True,
            "mode": mode,
            "applied": True,
            "reason": ai_result.get("reason", ""),
            "call_count": ai_result.get("call_count", 1),
            "selected_count": total_after_ai,
            "original_count": total_original,
            "max_calls": max_calls,
        }
        return final_result
