from .._shared import *


class _BuildEnhancedInputMixin:
    def _build_enhanced_input(self, collected_info: Dict[str, Any]) -> str:
        """
        构建增强的用户输入
        
        Args:
            collected_info: 收集的信息
        
        Returns:
            增强的输入文本
        """
        parts = []
        if "topic" in collected_info:
            parts.append(f"课题：{collected_info['topic']}")
        if "teaching_goals" in collected_info:
            parts.append(f"教学目标：{collected_info['teaching_goals']}")
        if "teaching_methods" in collected_info:
            parts.append(f"教学方法：{collected_info['teaching_methods']}")
        if "student_level" in collected_info:
            parts.append(f"学生水平：{collected_info['student_level']}")
        if "class_hours" in collected_info:
            parts.append(f"课时：{collected_info['class_hours']}")
        if "key_points" in collected_info:
            parts.append(f"教学重点：{collected_info['key_points']}")
        if "difficulties" in collected_info:
            parts.append(f"教学难点：{collected_info['difficulties']}")
        
        return "\n".join(parts)
