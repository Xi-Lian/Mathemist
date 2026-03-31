from .._shared import *


class _InitMixin:
    def __init__(self):
        """初始化教案生成器"""
        self.model_config = model_config
        
        # 加载优秀教案共性文件
        self.lesson_plan_common_characteristics = self._load_lesson_plan_common_characteristics()
        
        # 加载理论卡片文件
        self.theory_cards = self._load_theory_cards()
        
        # 解析理论卡片，建立索引
        self.theory_cards_index = self._parse_theory_cards()
        
        self.prompt_template = self._create_prompt_template()
