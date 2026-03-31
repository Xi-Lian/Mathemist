from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化意图分析器"""
        self.model_config = model_config
        self.prompt_template = self._create_prompt_template()
        self.context_history = []  # 上下文历史
