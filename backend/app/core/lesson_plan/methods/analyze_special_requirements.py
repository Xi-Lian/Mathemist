from .._shared import *


class _AnalyzeSpecialRequirementsMixin:
    def _analyze_special_requirements(self, user_input: str) -> List[str]:
        """
        分析用户输入中的特殊需求
        
        Args:
            user_input: 用户需求
        
        Returns:
            特殊需求列表
        """
        special_requirements = []
        
        # 定义特殊需求关键词
        requirements = {
            "核心素养": ["核心素养", "素养目标", "素养培养"],
            "分层教学": ["分层", "因材施教", "个性化"],
            "多媒体教学": ["多媒体", "课件", "视频", "动画"],
            "实验教学": ["实验", "实践", "操作"],
            "小组合作": ["小组", "合作", "讨论", "协作"]
        }
        
        # 匹配特殊需求
        for requirement, keywords in requirements.items():
            for keyword in keywords:
                if keyword in user_input:
                    special_requirements.append(requirement)
                    break
        
        return special_requirements
