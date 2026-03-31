from .._shared import *


class _CalculateTeachingValueMixin:
    def _calculate_teaching_value(self, structured: Dict[str, str]) -> float:
        """
        V10.0：计算教学价值
        
        基于教学目标的明确性、重难点的突出程度等
        """
        score = 0.0
        
        # 教学目标明确性
        objectives = structured.get("objectives", "")
        if objectives:
            # 检查是否包含具体的学习目标
            if any(keyword in objectives for keyword in ["理解", "掌握", "应用", "学会", "了解"]):
                score += 0.4
            else:
                score += 0.2
        
        # 重难点突出程度
        key_points = structured.get("key_points", "")
        if key_points:
            # 检查是否明确标注重点和难点
            if any(keyword in key_points for keyword in ["重点", "难点", "关键"]):
                score += 0.3
            else:
                score += 0.15
        
        # 教学过程的详细程度
        process = structured.get("process", "")
        if process:
            # 检查是否包含具体的教学步骤
            if any(keyword in process for keyword in ["步骤", "环节", "活动", "练习"]):
                score += 0.3
            else:
                score += 0.15
        
        # 确保分数在0-1之间
        return min(1.0, score)
