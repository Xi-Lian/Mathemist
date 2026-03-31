from .._shared import *


class _EnhanceWithContextMixin:
    def _enhance_with_context(self, query: str, result: Dict[str, Any]) -> Optional[str]:
        """
        V33.0改进：使用上下文增强查询
        
        Args:
            query: 原始查询
            result: 预处理结果
        
        Returns:
            增强后的查询
        """
        if not self.context_history:
            return None
        
        # 获取最近的上下文
        recent_context = self.context_history[-1]
        recent_query = recent_context.get("original_query", "")
        recent_concepts = recent_context.get("core_concepts", [])
        
        # 检查是否是上下文查询
        if "最近讲了" in query or "最近学了" in query:
            # 提取查询中的具体知识点
            specific_topics = []
            
            # 检查是否提到了具体的三角函数
            if "正弦" in query or "余弦" in query:
                specific_topics.extend(["正弦函数", "余弦函数"])
            elif "正切" in query:
                specific_topics.append("正切函数")
            elif "三角函数" in query:
                # 如果只说了三角函数，检查最近是否提到了具体的
                if "正弦" in recent_query or "余弦" in recent_query:
                    specific_topics.extend(["正弦函数", "余弦函数"])
                elif "正切" in recent_query:
                    specific_topics.append("正切函数")
                else:
                    specific_topics.append("三角函数")
            
            # 如果找到了具体主题，返回增强查询
            if specific_topics:
                enhanced_query = query
                for topic in specific_topics:
                    if topic not in enhanced_query:
                        enhanced_query += f" {topic}"
                return enhanced_query
        
        return None
