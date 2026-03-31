from .._shared import *


class _CalculateComprehensivenessMixin:
    def _calculate_comprehensiveness(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算综合性
        
        基于内容的全面性、涵盖的知识点等
        """
        score = 0.0
        
        # 内容全面性
        content_parts = 0
        if structured.get("objectives"):
            content_parts += 1
        if structured.get("key_points"):
            content_parts += 1
        if structured.get("process"):
            content_parts += 1
        
        # 根据内容部分数量计算分数
        if content_parts == 3:
            score += 0.6
        elif content_parts == 2:
            score += 0.4
        elif content_parts == 1:
            score += 0.2
        
        # 检查是否包含多个教学环节
        process = structured.get("process", "")
        if process:
            # 简单判断：检查是否包含多个段落或环节
            if process.count('\n') >= 3:
                score += 0.4
            elif process.count('\n') >= 1:
                score += 0.2
        
        # 确保分数在0-1之间
        return min(1.0, score)
