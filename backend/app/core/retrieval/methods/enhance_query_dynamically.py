from .._shared import *


class _EnhanceQueryDynamicallyMixin:
    def _enhance_query_dynamically(self, query: str, detected_intents: List[Dict[str, Any]]) -> str:
        """
        根据检测到的意图动态增强查询
        
        Args:
            query: 原始查询
            detected_intents: 检测到的意图列表
            
        Returns:
            增强后的查询
        """
        if not detected_intents:
            # V52.0改进：即使没有检测到意图，也进行基础增强
            return self._basic_query_enhancement(query)
        
        enhanced_parts = [query]
        added_keywords = set()
        
        # 根据优先级添加关键词
        for intent in detected_intents:
            for keyword in intent["keywords"]:
                if keyword not in added_keywords and keyword not in query:
                    enhanced_parts.append(keyword)
                    added_keywords.add(keyword)
        
        enhanced_query = " ".join(enhanced_parts)
        
        # V52.0改进：添加基础增强
        enhanced_query = self._basic_query_enhancement(enhanced_query)
        
        print(f"   🔍 V51.0动态查询增强: '{query}' -> '{enhanced_query}'")
        print(f"   🔍 V51.0检测到的意图: {[i['name'] for i in detected_intents]}")
        
        return enhanced_query
    
    # V52.0改进：基础查询增强
