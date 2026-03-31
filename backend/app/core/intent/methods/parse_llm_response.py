from .._shared import *


class _ParseLlmResponseMixin:
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
            parsed = json.loads(cleaned)
            primary_intent = parsed.get("primary_intent", self.INTENT_SEARCH)
            intents = parsed.get("intents", [])
            user_needs = parsed.get("user_needs", "")
            resource_types = parsed.get("resource_types", [])
            
            # 验证intents格式
            if not isinstance(intents, list):
                intents = [{"type": self.INTENT_SEARCH, "confidence": 1.0}]
            
            print(f"📋 主要意图: {primary_intent}")
            print(f"📋 用户需求: {user_needs}")
            print(f"📋 资源类型: {resource_types}")
            print(f"📋 所有意图: {intents}")
            
            return {
                "intent": primary_intent,
                "user_needs": user_needs,
                "resource_types": resource_types,
                "intents": intents,
                "current_step": "intent_understanding",
                "error": None
            }
        except json.JSONDecodeError as e:
            print(f"⚠️ JSON解析失败: {e}")
            raise
