from .._shared import *


class _DetectQueryIntentsMixin:
    def _detect_query_intents(self, query: str) -> List[Dict[str, Any]]:
        """
        动态识别查询意图
        
        Args:
            query: 用户查询
            
        Returns:
            识别到的意图列表，按优先级排序
        """
        detected_intents = []
        query_lower = query.lower()
        
        for intent_name, intent_config in self.query_intent_patterns.items():
            # 检查是否匹配任何模式
            matched_patterns = []
            for pattern in intent_config["patterns"]:
                if pattern in query:
                    matched_patterns.append(pattern)
            
            if matched_patterns:
                detected_intents.append({
                    "name": intent_name,
                    "priority": intent_config["priority"],
                    "matched_patterns": matched_patterns,
                    "keywords": intent_config["keywords"],
                    "resource_indicators": intent_config["resource_indicators"]
                })
        
        # 按优先级排序（高优先级在前）
        detected_intents.sort(key=lambda x: x["priority"], reverse=True)
        
        return detected_intents
    
    # V51.0改进：动态生成增强查询
