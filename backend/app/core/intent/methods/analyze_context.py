from .._shared import *


class _AnalyzeContextMixin:
    def _analyze_context(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户输入的上下文
        
        Args:
            user_input: 用户输入文本
        
        Returns:
            上下文分析结果
        """
        context_analysis = {
            "context_type": "normal",
            "context_keywords": [],
            "suggestions": []
        }
        
        # 分析上下文类型
        for context_type, keywords in self.CONTEXT_INTENT_PATTERNS.items():
            matched_keywords = [kw for kw in keywords if kw in user_input]
            if matched_keywords:
                context_analysis["context_type"] = context_type
                context_analysis["context_keywords"] = matched_keywords
                
                # 根据上下文类型生成建议
                if context_type == "continue":
                    context_analysis["suggestions"].append("保持当前主题，增加更多资源")
                elif context_type == "refine":
                    context_analysis["suggestions"].append("调整搜索参数，提供更精准的资源")
                elif context_type == "specific":
                    context_analysis["suggestions"].append("提供更详细的资源内容")
                elif context_type == "difficulty":
                    context_analysis["suggestions"].append("根据难度要求筛选资源")
                elif context_type == "quantity":
                    context_analysis["suggestions"].append("根据数量要求限制结果")
                break
        
        # 分析最近上下文
        if self.context_history:
            recent_context = self.context_history[-1]
            if recent_context:
                clarified_topic = recent_context.get("clarified_topic", {})
                if clarified_topic and "主题" in clarified_topic or "resource_types" in recent_context:
                    context_analysis["recent_context"] = recent_context
        
        return context_analysis
