from .._shared import *


class _CalculateContentCompletenessMixin:
    def _calculate_content_completeness(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算内容完整性
        
        基于各章节内容的完整性
        """
        score = 0.0
        
        # 教学目标完整性
        objectives = structured.get("objectives", "")
        if objectives:
            if len(objectives) > 200:
                score += 0.3
            elif len(objectives) > 100:
                score += 0.2
            else:
                score += 0.1
        
        # 教学重难点完整性
        key_points = structured.get("key_points", "")
        if key_points:
            if len(key_points) > 150:
                score += 0.3
            elif len(key_points) > 75:
                score += 0.2
            else:
                score += 0.1
        
        # 教学过程完整性
        process = structured.get("process", "")
        if process:
            if len(process) > 500:
                score += 0.4
            elif len(process) > 250:
                score += 0.3
            elif len(process) > 100:
                score += 0.2
            else:
                score += 0.1
        
        # 确保分数在0-1之间
        return min(1.0, score)
