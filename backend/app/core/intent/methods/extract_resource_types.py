from .._shared import *

# V53.0：课件教学用途关键词，这些词出现时应识别为课件而非习题
# "练习课课件"、"复习课课件"、"新授课课件" 等模式中的"练习/复习"不应触发习题类型
_COURSEWARE_TEACHING_USE_PATTERNS = ["练习课", "复习课", "习题课", "新授课"]


class _ExtractResourceTypesMixin:
    def _extract_resource_types(self, user_input: str) -> List[str]:
        """
        从用户输入中提取资源类型
        
        Args:
            user_input: 用户输入
        
        Returns:
            资源类型列表
        """
        resource_types = []
        
        # 资源类型关键词映射
        # V52.0改进：添加"例子"作为习题类型，因为用户说"例子"时通常是指习题例子
        type_keywords = {
            "资料": ["资料", "资源"],
            "习题": ["习题", "题目", "练习", "练习题", "测试", "测试题", "作业", "试题", "考题", "填空题", "选择题", "解答题", "计算题", "证明题", "应用题", "作图题", "例子", "实例", "案例"],
            "教案": ["教案", "教学设计", "备课", "教学计划"],
            "课件": ["课件", "PPT", "幻灯片"],
            "课例": ["课例", "教学案例", "视频课", "课堂实录"],
            "GGB": ["GGB", "GeoGebra", "动态图", "可视化", "动态演示"],
            "教学大纲": ["教学大纲", "课程标准", "教学要求"]
        }
        
        # 对于中文输入，不需要转换为小写，直接使用原始输入
        # 对于英文输入，转换为小写以确保匹配
        user_input_processed = user_input.lower() if any(c.isalpha() for c in user_input) else user_input
        
        # V53.0：检查用户输入是否包含课件教学用途模式（如"练习课"、"复习课"等）
        # 若包含，则"练习"、"复习"等词不应触发习题类型，而应触发课件类型
        has_courseware_teaching_use = any(pat in user_input for pat in _COURSEWARE_TEACHING_USE_PATTERNS)
        
        # 检查每种资源类型
        for resource_type, keywords in type_keywords.items():
            if resource_type == "习题" and has_courseware_teaching_use:
                # V53.0修复：用户输入含课件教学用途模式时，跳过"练习"/"复习"等词的习题触发
                # 仅保留不会与课件用途混淆的习题专属词汇
                exercise_only_keywords = [
                    kw for kw in keywords
                    if kw not in ("练习", "复习")
                    and not any(pat.startswith(kw) for pat in _COURSEWARE_TEACHING_USE_PATTERNS)
                ]
                if any(keyword in user_input_processed for keyword in exercise_only_keywords):
                    resource_types.append(resource_type)
                # 同时强制加入课件类型（因为含有"练习课"/"复习课"等词暗示要找课件）
                if "课件" not in resource_types:
                    resource_types.append("课件")
            else:
                if any(keyword in user_input_processed for keyword in keywords):
                    resource_types.append(resource_type)
        
        return resource_types
