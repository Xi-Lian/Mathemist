from .._shared import *


class _BackupExtractInfoMixin:
    def _backup_extract_info(self, user_input: str, existing_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        备用信息提取方法 - 基于关键词的简单提取
        
        当大模型提取失败时使用
        
        Args:
            user_input: 用户输入
            existing_info: 已有信息
        
        Returns:
            提取的信息
        """
        extracted = {}
        
        # 简单关键词匹配
        import re
        
        # 年级/学生水平
        if "student_level" not in existing_info:
            grade_patterns = [
                (r'高[一二三四]', '高一'),
                (r'初[一二三]', '初一'),
                (r'高(\d+)', lambda m: f'高{m.group(1)}'),
                (r'初(\d+)', lambda m: f'初{m.group(1)}'),
            ]
            
            for pattern, replacement in grade_patterns:
                match = re.search(pattern, user_input)
                if match:
                    if callable(replacement):
                        extracted["student_level"] = replacement(match)
                    else:
                        extracted["student_level"] = replacement
                    break
        
        # 课时
        if "class_hours" not in existing_info:
            hour_patterns = [
                (r'(\d+)\s*课时?', lambda m: f'{m.group(1)}课时'),
                (r'(\d+)\s*小时?', lambda m: f'{m.group(1)}小时'),
            ]
            
            for pattern, replacement in hour_patterns:
                match = re.search(pattern, user_input)
                if match:
                    if callable(replacement):
                        extracted["class_hours"] = replacement(match)
                    else:
                        extracted["class_hours"] = replacement
                    break
        
        # 教学方法关键词
        if "teaching_methods" not in existing_info:
            method_keywords = ['探究式', '讲授式', '合作学习', '问题解决', '启发式', '讨论式', '演示法', '练习法']
            found_methods = [kw for kw in method_keywords if kw in user_input]
            if found_methods:
                extracted["teaching_methods"] = '、'.join(found_methods)
        
        # 教学目标
        if "teaching_goals" not in existing_info:
            if any(keyword in user_input for keyword in ["目标", "学会", "掌握", "理解"]):
                extracted["teaching_goals"] = user_input
        
        # 教学重点
        if "key_points" not in existing_info:
            if any(keyword in user_input for keyword in ["重点", "关键", "核心"]):
                extracted["key_points"] = user_input
        
        # 教学难点
        if "difficulties" not in existing_info:
            if any(keyword in user_input for keyword in ["难点", "困难", "难以理解"]):
                extracted["difficulties"] = user_input
        
        # 课题
        if "topic" not in existing_info:
            extracted["topic"] = user_input
        
        return extracted
