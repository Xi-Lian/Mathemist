from .._shared import *


class _FormatLessonPlanPatternsMixin:
    def _format_lesson_plan_patterns(self, patterns: List[Dict[str, Any]]) -> str:
        """
        格式化教案示例，突出优秀教案的共性特征
        
        Args:
            patterns: 教案示例列表
        
        Returns:
            格式化后的文本
        """
        if not patterns:
            return "暂无优秀教案示例"
        
        formatted = []
        for i, pattern in enumerate(patterns, 1):
            title = pattern.get("title", f"教案{i}")
            content = pattern.get("content", "")
            
            # 提取关键信息
            formatted.append(f"""
【优秀教案示例{i}】{title}

{content}

---
""")
        
        return "\n".join(formatted)
