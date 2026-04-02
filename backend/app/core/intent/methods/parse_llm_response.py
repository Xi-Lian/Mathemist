from .._shared import *


class _ParseLlmResponseMixin:
    def _normalize_primary_intent(self, value: Any) -> str:
        text = str(value or "").strip()
        if text in {
            self.INTENT_SEARCH,
            self.INTENT_LESSON_PLAN,
            self.INTENT_VISUALIZATION,
            self.INTENT_CONVERSATION,
        }:
            return text

        text_lower = text.lower()
        if "conversation" in text_lower or "chat" in text_lower or "闲聊" in text or "对话" in text:
            return self.INTENT_CONVERSATION
        if "visual" in text_lower or "ggb" in text_lower:
            return self.INTENT_VISUALIZATION
        if "lesson" in text_lower or "教案" in text:
            return self.INTENT_LESSON_PLAN
        return self.INTENT_SEARCH

    def _normalize_resource_types(self, value: Any) -> List[str]:
        if isinstance(value, str):
            candidates = re.split(r"[,，/、\s]+", value)
        elif isinstance(value, list):
            candidates = [str(item).strip() for item in value]
        else:
            candidates = []

        allowed = {"习题", "教案", "课件", "课例", "GGB", "教学大纲", "资料"}
        return [item for item in candidates if item in allowed]

    def _normalize_intents(self, intents: Any, primary_intent: str) -> List[Dict[str, Any]]:
        normalized: List[Dict[str, Any]] = []
        if isinstance(intents, list):
            for item in intents:
                if not isinstance(item, dict):
                    continue
                intent_type = self._normalize_primary_intent(item.get("type"))
                try:
                    confidence = float(item.get("confidence", 0.0))
                except (TypeError, ValueError):
                    confidence = 0.0
                confidence = max(0.0, min(confidence, 1.0))
                normalized.append({"type": intent_type, "confidence": confidence})

        if not normalized:
            fallbacks = {
                self.INTENT_SEARCH: [
                    {"type": self.INTENT_SEARCH, "confidence": 0.9},
                    {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                    {"type": self.INTENT_VISUALIZATION, "confidence": 0.1},
                    {"type": self.INTENT_CONVERSATION, "confidence": 0.1},
                ],
                self.INTENT_LESSON_PLAN: [
                    {"type": self.INTENT_LESSON_PLAN, "confidence": 0.9},
                    {"type": self.INTENT_SEARCH, "confidence": 0.1},
                    {"type": self.INTENT_VISUALIZATION, "confidence": 0.1},
                    {"type": self.INTENT_CONVERSATION, "confidence": 0.1},
                ],
                self.INTENT_VISUALIZATION: [
                    {"type": self.INTENT_VISUALIZATION, "confidence": 0.9},
                    {"type": self.INTENT_SEARCH, "confidence": 0.1},
                    {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                    {"type": self.INTENT_CONVERSATION, "confidence": 0.1},
                ],
                self.INTENT_CONVERSATION: [
                    {"type": self.INTENT_CONVERSATION, "confidence": 0.9},
                    {"type": self.INTENT_SEARCH, "confidence": 0.2},
                    {"type": self.INTENT_LESSON_PLAN, "confidence": 0.1},
                    {"type": self.INTENT_VISUALIZATION, "confidence": 0.1},
                ],
            }
            return fallbacks.get(primary_intent, fallbacks[self.INTENT_SEARCH])

        if not any(item["type"] == primary_intent for item in normalized):
            normalized.insert(0, {"type": primary_intent, "confidence": 0.9})

        normalized.sort(key=lambda item: item["confidence"], reverse=True)
        return normalized[:4]

    def _build_result_from_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        primary_intent = self._normalize_primary_intent(payload.get("primary_intent"))
        user_needs = str(payload.get("user_needs") or "").strip()
        resource_types = self._normalize_resource_types(payload.get("resource_types"))
        intents = self._normalize_intents(payload.get("intents"), primary_intent)

        return {
            "intent": primary_intent,
            "user_needs": user_needs,
            "resource_types": resource_types,
            "intents": intents,
            "current_step": "intent_understanding",
            "error": None,
        }

    def _parse_non_json_response(self, response: str) -> Dict[str, Any]:
        text = (response or "").strip()
        if not text:
            raise ValueError("empty_llm_response")

        primary_intent = self._normalize_primary_intent(text)
        resource_types = self._normalize_resource_types(text)
        if primary_intent == self.INTENT_VISUALIZATION and "GGB" not in resource_types:
            resource_types.append("GGB")

        result = self._get_default_intent(None, text[:80], resource_types)
        result["intent"] = primary_intent
        result["intents"] = self._normalize_intents([], primary_intent)
        result["error"] = None
        return result

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """
        解析LLM响应
        
        Args:
            response: 模型响应文本
        
        Returns:
            解析后的意图结果
        """
        try:
            cleaned = self._clean_json_response(response)
            if not cleaned:
                raise ValueError("empty_llm_response")

            parsed = json.loads(cleaned)
            if isinstance(parsed, list):
                parsed = next((item for item in parsed if isinstance(item, dict)), {})
            if not isinstance(parsed, dict):
                raise ValueError("invalid_llm_payload")

            result = self._build_result_from_payload(parsed)
            print(f"📋 主要意图: {result['intent']}")
            print(f"📋 用户需求: {result['user_needs']}")
            print(f"📋 资源类型: {result['resource_types']}")
            print(f"📋 所有意图: {result['intents']}")
            return result
        except json.JSONDecodeError:
            print("⚠️ JSON解析失败，尝试非JSON兼容解析")
            return self._parse_non_json_response(response)
