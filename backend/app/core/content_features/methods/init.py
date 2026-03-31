from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化内容特征提取器"""
        # V12.0新增：初始化主观意图解释器
        self.subjective_interpreter = SubjectiveIntentInterpreter()
