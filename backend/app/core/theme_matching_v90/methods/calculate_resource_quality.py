from .._shared import *


class _CalculateResourceQualityMixin:
    def _calculate_resource_quality(self, lesson_title: str, lesson_content: str, structured: Dict[str, str]) -> float:
        """
        V10.0：计算资源质量
        
        基于标题质量、内容长度、结构完整性等因素
        """
        score = 0.0
        
        # 标题质量（长度、专业性）
        if lesson_title and len(lesson_title) >= 5:
            score += 0.3
        
        # 内容长度
        content_length = len(lesson_content)
        if content_length > 1000:
            score += 0.3
        elif content_length > 500:
            score += 0.2
        elif content_length > 200:
            score += 0.1
        
        # 结构完整性
        structure_score = 0.0
        if structured.get("objectives"):
            structure_score += 0.1
        if structured.get("key_points"):
            structure_score += 0.1
        if structured.get("process"):
            structure_score += 0.1
        score += structure_score
        
        # 确保分数在0-1之间
        return min(1.0, score)
