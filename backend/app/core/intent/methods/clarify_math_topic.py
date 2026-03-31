from .._shared import *


class _ClarifyMathTopicMixin:
    def _clarify_math_topic(self, user_input: str) -> Optional[Dict[str, Any]]:
        """
        V33.0: 澄清数学主题，解决概念混淆问题
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            澄清后的主题信息
        """
        for topic, config in self.V33_MATH_TOPIC_CLARIFICATION.items():
            core_matched = any(kw in user_input for kw in config.get("core_keywords", []))
            exclude_matched = any(kw in user_input for kw in config.get("exclude_keywords", []))
            
            if core_matched:
                return {
                    "topic": topic,
                    "is_confused": exclude_matched,
                    "description": config.get("description", ""),
                    "should_exclude": exclude_matched,
                    "exclude_keywords_matched": [kw for kw in config.get("exclude_keywords", []) if kw in user_input] if exclude_matched else []
                }
        return None
