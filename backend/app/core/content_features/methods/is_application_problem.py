from .._shared import *


class _IsApplicationProblemMixin:
    def is_application_problem(self, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        检测题目是否是应用题
        
        Args:
            content: 题目内容
            metadata: 题目元数据
            
        Returns:
            是否是应用题
        """
        # 首先检查元数据中的题目类型
        if metadata:
            exercise_type = metadata.get('题目类型', '')
            if exercise_type:
                for keyword in self.EXERCISE_TYPES['应用题']:
                    if keyword in exercise_type:
                        return True
        
        # 检查内容中的应用题场景关键词
        if content:
            for scene, keywords in self.APPLICATION_SCENES.items():
                for keyword in keywords:
                    if keyword in content:
                        return True
        
        # 检查内容中的应用相关关键词
        for keyword in self.EXERCISE_TYPES['应用题']:
            if keyword in content:
                return True
        
        return False
