from .._shared import *


class _CheckTheoryDiversityMixin:
    def _check_theory_diversity(self, lesson_plan: str) -> str:
        """
        检查教案中的理论多样性
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            检查后的教案内容
        """
        # 监控理论使用频率
        frequency = self._monitor_theory_frequency(lesson_plan)
        
        # 计算总引用次数
        total_references = sum(frequency.values())
        if total_references == 0:
            return lesson_plan
        
        # 检查是否有理论使用过度（超过30%）
        overused_theories = []
        for theory, count in frequency.items():
            if count / total_references > 0.3:
                overused_theories.append(theory)
        
        # 如果有过度使用的理论，进行替换建议
        if overused_theories:
            print(f"⚠️  检测到过度使用的理论: {overused_theories}")
            # 这里可以添加替换逻辑，暂时只打印警告
        
        return lesson_plan
