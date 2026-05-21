from .._shared import *

# V53.0：课件教学用途映射表
# key 为数据库 `教学用途` 字段中的标准值（前缀匹配），value 为触发该用途的查询关键词列表
_TEACHING_USE_MAP = {
    "新授课": ["新授课", "新课"],
    "练习课": ["练习课"],
    "复习课": ["复习课", "复习"],
    "习题课": ["习题课"],
}

# 触发"课件"时需要排除纯复习词（如"复习一下"中的"复习"不代表要找复习课课件）
# 因此"复习"只有在同时出现"课件"/"PPT"等词时才触发"复习课"教学用途
_COURSEWARE_SIGNALS = ["课件", "ppt", "PPT", "幻灯片"]


class _ExtractCoursewareTeachingUseMixin:
    def _extract_courseware_teaching_use(self, user_input: str) -> Optional[str]:
        """
        从用户输入中提取期望的课件教学用途。

        Returns:
            匹配到的教学用途字符串（如 "练习课"），或 None（用户未指定）。
        """
        if not user_input:
            return None

        has_courseware_signal = any(sig in user_input for sig in _COURSEWARE_SIGNALS)

        for usage_key, triggers in _TEACHING_USE_MAP.items():
            for trigger in triggers:
                if trigger in user_input:
                    # 对于"复习"这个词（非"复习课"精确词），需要额外确认有课件信号
                    if trigger == "复习" and not has_courseware_signal:
                        continue
                    return usage_key

        return None
