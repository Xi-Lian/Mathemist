import json
from typing import Any, Dict, List, Tuple

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from ...model_config import model_config


def _is_rate_limit_error(exc: Exception) -> bool:
    text = f"{type(exc).__name__}:{exc}".lower()
    return "ratelimit" in text or "429" in text or "too many requests" in text


def _flatten_resources(classified: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    flat: List[Tuple[str, Dict[str, Any]]] = []
    for category, resources in classified.items():
        if not isinstance(resources, list):
            continue
        for resource in resources:
            if isinstance(resource, dict):
                flat.append((category, resource))
    return flat


def _build_candidates_payload(flat: List[Tuple[str, Dict[str, Any]]], max_candidates: int = 36) -> List[Dict[str, Any]]:
    payload: List[Dict[str, Any]] = []
    for index, (category, resource) in enumerate(flat[:max_candidates], start=1):
        payload.append(
            {
                "candidate_id": f"C{index}",
                "origin_category": category,
                "title": resource.get("title", ""),
                "resource_type": resource.get("resource_type", ""),
                "knowledge_tags": resource.get("knowledge_tags", ""),
                "summary": resource.get("summary", "") or (resource.get("content", "") or "")[:220],
                "source": resource.get("source", "") or resource.get("source_file", ""),
                "relevance": float(resource.get("relevance", 0.0) or 0.0),
            }
        )
    return payload


def _parse_json_result(raw_text: str) -> Dict[str, Any]:
    text = (raw_text or "").strip()
    if not text:
        return {}
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except Exception:
                return {}
    return {}


def _build_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_template(
        """
你是数学教学资源检索助手。请基于用户查询，从候选资源中筛选并重排。

用户查询：{query}
意图：{intent}
资源类型偏好：{resource_types}
核心主题：{core_theme}

候选资源(JSON)：
{candidates_json}

要求：
1) 仅返回 JSON，不要返回其它文本。
2) JSON 格式必须是：
{{
  "selected_ids": ["C1", "C3"],
  "reason": "一句话说明筛选依据"
}}
3) selected_ids 顺序代表最终排序。
4) 若无合适候选，返回空数组。
"""
    )


def _rerank_once(
    query: str,
    intent: str,
    resource_types: List[str],
    core_theme: str,
    candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    try:
        model = model_config.get_model("intent")
    except Exception as e:
        raise RuntimeError("intent_model_unavailable") from e
    if model is None:
        raise RuntimeError("intent_model_unavailable")
    chain = _build_prompt() | model | StrOutputParser()
    result_text = chain.invoke(
        {
            "query": query,
            "intent": intent,
            "resource_types": ",".join(resource_types or []),
            "core_theme": core_theme or "",
            "candidates_json": json.dumps(candidates, ensure_ascii=False),
        }
    )
    return _parse_json_result(result_text)


def apply_ai_screen_and_rerank(
    classified: Dict[str, Any],
    query: str,
    intent: str,
    resource_types: List[str],
    core_theme: str,
    max_calls: int = 3,
) -> Dict[str, Any]:
    flat = _flatten_resources(classified)
    if not flat:
        return {"ok": False, "reason": "empty_candidates", "result": classified}

    candidates = _build_candidates_payload(flat)
    if not candidates:
        return {"ok": False, "reason": "empty_payload", "result": classified}

    last_reason = "ai_unavailable"
    max_calls = max(1, min(int(max_calls or 1), 3))
    for call_index in range(max_calls):
        try:
            parsed = _rerank_once(query, intent, resource_types or [], core_theme or "", candidates)
            selected_ids = parsed.get("selected_ids") if isinstance(parsed, dict) else None
            if not isinstance(selected_ids, list):
                last_reason = "invalid_ai_response"
                continue
            selected_ids = [item for item in selected_ids if isinstance(item, str)]

            mapping = {item["candidate_id"]: (cat, res) for item, (cat, res) in zip(candidates, flat)}
            selected_pairs = [mapping[item_id] for item_id in selected_ids if item_id in mapping]

            if not selected_pairs:
                last_reason = "no_selected_candidates"
                continue

            rebuilt: Dict[str, Any] = {}
            for key, value in classified.items():
                rebuilt[key] = [] if isinstance(value, list) else value

            for category, resource in selected_pairs:
                rebuilt.setdefault(category, [])
                rebuilt[category].append(resource)

            for key, value in classified.items():
                if not isinstance(value, list):
                    continue
                if key not in rebuilt:
                    rebuilt[key] = []

            return {
                "ok": True,
                "reason": parsed.get("reason", ""),
                "call_count": call_index + 1,
                "selected_count": len(selected_pairs),
                "result": rebuilt,
                "selected_ids": [item for item in selected_ids if item in mapping],
            }
        except Exception as e:
            last_reason = f"ai_exception:{type(e).__name__}"
            if _is_rate_limit_error(e):
                return {"ok": False, "reason": "ai_rate_limited", "call_count": call_index + 1, "result": classified}
            continue

    return {"ok": False, "reason": last_reason, "call_count": max_calls, "result": classified}
