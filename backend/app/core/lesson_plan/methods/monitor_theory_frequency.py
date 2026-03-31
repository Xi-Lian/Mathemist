from .._shared import *


class _MonitorTheoryFrequencyMixin:
    def _monitor_theory_frequency(self, lesson_plan: str) -> Dict[str, int]:
        """
        监控教案中理论的使用频率
        
        Args:
            lesson_plan: 教案内容
        
        Returns:
            理论使用频率字典，格式为：{"理论卡片1": 3, "理论卡片2": 2, ...}
        """
        import re
        frequency = {}
        
        # 匹配理论卡片引用的正则表达式
        pattern = r"理论卡片(\d+)"
        matches = re.findall(pattern, lesson_plan)
        
        for card_number in matches:
            card_key = f"理论卡片{card_number}"
            if card_key in frequency:
                frequency[card_key] += 1
            else:
                frequency[card_key] = 1
        
        return frequency
